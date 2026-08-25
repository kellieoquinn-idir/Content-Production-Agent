"""Sequential Fieldstone pipeline: researcher → writer → editor, with retry.

If the editor/critic says REVISE twice, stop and flag a human editor.
The writer gets one chance to fix notes in between those two reviews.
"""

import argparse
import sys
import time
from datetime import datetime

import critic
import observability
from agents.editor import build_editor_agent
from agents.researcher import build_researcher_agent
from agents.writer import build_writer_agent
from llm import require_api_key


def last_text(result) -> str:
    content = result["messages"][-1].content
    if isinstance(content, str):
        return content
    return str(content)


def _clock() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _tool_names(messages) -> list[str]:
    names = []
    for message in messages:
        for tc in getattr(message, "tool_calls", None) or []:
            names.append(tc["name"])
    return names


def invoke_and_log(run_id, agent_name, agent, payload, timings, trace=False, label=None):
    shown = label or agent_name
    print(f"[{_clock()}] {shown} started")
    started = time.perf_counter()
    try:
        result = agent.invoke(payload)
    except Exception as exc:
        duration_s = time.perf_counter() - started
        timings[agent_name] = timings.get(agent_name, 0) + duration_s
        print(f"[{_clock()}] {shown} failed  {duration_s:.2f}s  error: {exc}")
        raise
    duration_s = time.perf_counter() - started
    timings[agent_name] = timings.get(agent_name, 0) + duration_s
    observability.record_agent_run(run_id, agent_name, result["messages"], duration_s)

    extra = ""
    tools = _tool_names(result["messages"])
    if tools:
        extra += f"  tools: {', '.join(tools)}"
    print(f"[{_clock()}] {shown} finished  {duration_s:.2f}s{extra}")

    if trace:
        observability.print_agent_trace(shown, result["messages"], duration_s)
    return result


def _writer_payload(topic, research_brief, editor_notes=None, previous_draft=None):
    if editor_notes:
        return {
            "messages": [{
                "role": "user",
                "content": (
                    f"Revise this travel blog post about: {topic}\n\n"
                    "The editor rejected the draft. Fix every issue in the "
                    "notes. Use only the research brief. Do not invent facts.\n\n"
                    f"RESEARCH BRIEF:\n{research_brief}\n\n"
                    f"PREVIOUS DRAFT:\n{previous_draft}\n\n"
                    f"EDITOR NOTES:\n{editor_notes}"
                ),
            }]
        }
    return {
        "messages": [{
            "role": "user",
            "content": (
                f"Write a travel blog post about: {topic}\n\n"
                "Use only the research brief below. Do not invent facts.\n\n"
                f"RESEARCH BRIEF:\n{research_brief}"
            ),
        }]
    }


def _editor_payload(topic, research_brief, draft):
    return {
        "messages": [{
            "role": "user",
            "content": (
                f"Review this draft against the research brief for: {topic}\n\n"
                f"{critic.EDITOR_CHECKLIST}\n\n"
                f"RESEARCH BRIEF:\n{research_brief}\n\n"
                f"DRAFT:\n{draft}"
            ),
        }]
    }


def run_pipeline(topic: str, trace: bool = False) -> dict:
    require_api_key()

    run_id = observability.new_run_id()
    timings = {}
    retry_history = []

    researcher = build_researcher_agent()
    writer = build_writer_agent()
    editor = build_editor_agent()

    research_result = invoke_and_log(
        run_id,
        "researcher",
        researcher,
        {
            "messages": [{
                "role": "user",
                "content": (
                    f"Research this travel blog topic: {topic}. "
                    "Use the search_sources tool. Produce a brief with at least "
                    "5 facts and citations from the tool results."
                ),
            }]
        },
        timings,
        trace=trace,
    )
    research_brief = last_text(research_result)

    write_result = invoke_and_log(
        run_id, "writer", writer,
        _writer_payload(topic, research_brief),
        timings, trace=trace,
    )
    draft = last_text(write_result)

    retry_count = 0
    revise_count = 0
    decision = "UNKNOWN"
    editor_verdict = ""
    editor_result = None
    human_review_reason = None

    while True:
        editor_label = "editor" if retry_count == 0 else f"editor retry {retry_count}"
        editor_result = invoke_and_log(
            run_id, "editor", editor,
            _editor_payload(topic, research_brief, draft),
            timings, trace=trace, label=editor_label,
        )
        editor_verdict = last_text(editor_result)
        decision, editor_verdict = critic.apply_critic(editor_verdict, draft)
        print(f"[{_clock()}] critic decision: {decision}")

        retry_history.append({
            "attempt": retry_count,
            "decision": decision,
            "verdict": editor_verdict,
        })

        if decision == "PASS":
            break

        if decision == "UNKNOWN":
            human_review_reason = "Editor verdict was unclear (not PASS or REVISE)."
            print(f"[{_clock()}] {human_review_reason} Flagging for a human editor.")
            break

        revise_count += 1
        print(f"[{_clock()}] REVISE count: {revise_count}/{critic.REVISE_LIMIT}")

        if revise_count >= critic.REVISE_LIMIT:
            human_review_reason = (
                "Editor said REVISE twice. A human editor needs to look at this draft."
            )
            print()
            print("=" * 60)
            print("FLAGGED FOR HUMAN EDITOR")
            print("=" * 60)
            print(human_review_reason)
            break

        retry_count += 1
        print(f"[{_clock()}] sending draft back to writer (retry {retry_count})")
        write_result = invoke_and_log(
            run_id, "writer", writer,
            _writer_payload(topic, research_brief, editor_verdict, draft),
            timings, trace=trace,
            label=f"writer retry {retry_count}",
        )
        draft = last_text(write_result)

    requires_human_review = decision != "PASS"

    observability.print_run_summary(run_id, timings)

    return {
        "topic": topic,
        "research_brief": research_brief,
        "draft": draft,
        "editor_verdict": editor_verdict,
        "decision": decision,
        "retry_count": retry_count,
        "revise_count": revise_count,
        "requires_human_review": requires_human_review,
        "human_review_reason": human_review_reason,
        "retry_history": retry_history,
        "traces": {
            "researcher": research_result["messages"],
            "writer": write_result["messages"],
            "editor": editor_result["messages"] if editor_result else [],
        },
        "run_id": run_id,
        "timings": timings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Fieldstone content pipeline.")
    parser.add_argument(
        "topic",
        nargs="?",
        default="best time to visit Lisbon",
        help="Travel blog topic",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Print the full agent message trace (for observability)",
    )
    args = parser.parse_args()

    print(f"Topic: {args.topic}\n")
    result = run_pipeline(args.topic, trace=args.trace)

    print("=" * 60)
    print("1. RESEARCH BRIEF")
    print("=" * 60)
    print(result["research_brief"])
    print()
    print("=" * 60)
    print("2. WRITER DRAFT")
    print("=" * 60)
    print(result["draft"])
    print()
    print("=" * 60)
    print("3. EDITOR VERDICT")
    print("=" * 60)
    print(result["editor_verdict"])
    print()
    print("=" * 60)
    print(
        f"DECISION: {result['decision']}  "
        f"REVISE count: {result['revise_count']}/{critic.REVISE_LIMIT}  "
        f"human editor: {result['requires_human_review']}"
    )
    if result.get("human_review_reason"):
        print(result["human_review_reason"])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:
        print(f"Pipeline stopped without crashing the process: {exc}")
        sys.exit(1)
