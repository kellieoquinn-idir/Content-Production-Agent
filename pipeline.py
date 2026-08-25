"""Sequential Fieldstone pipeline: researcher → writer → editor.

Integration owns this handoff. Jared's orchestrator can call run_pipeline()
later for parallel start / routing. Ayoka owns retry rules; this file does
one editor pass and stops.

Handoff shape:
    topic: str
    research_brief: str   # researcher final text, ≥5 cited facts
    draft: str            # writer final text, ≥300 words
    editor_verdict: str   # editor final text, should include PASS or REVISE
    traces: dict          # each invoke's messages
    run_id: str           # observability run tag
    timings: dict         # seconds per agent
"""

import argparse
import sys
import time

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


def invoke_and_log(run_id, agent_name, agent, payload, timings, trace=False):
    started = time.perf_counter()
    result = agent.invoke(payload)
    duration_s = time.perf_counter() - started
    timings[agent_name] = duration_s
    observability.record_agent_run(run_id, agent_name, result["messages"], duration_s)
    if trace:
        observability.print_agent_trace(agent_name, result["messages"], duration_s)
    return result


def run_pipeline(topic: str, trace: bool = False) -> dict:
    require_api_key()

    run_id = observability.new_run_id()
    timings = {}

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
        run_id,
        "writer",
        writer,
        {
            "messages": [{
                "role": "user",
                "content": (
                    f"Write a travel blog post about: {topic}\n\n"
                    "Use only the research brief below. Do not invent facts.\n\n"
                    f"RESEARCH BRIEF:\n{research_brief}"
                ),
            }]
        },
        timings,
        trace=trace,
    )
    draft = last_text(write_result)

    editor_result = invoke_and_log(
        run_id,
        "editor",
        editor,
        {
            "messages": [{
                "role": "user",
                "content": (
                    f"Review this draft against the research brief for: {topic}\n\n"
                    "Fact-check the draft against the brief. Check grammar and "
                    "readability. End with a clear decision: PASS or REVISE.\n\n"
                    f"RESEARCH BRIEF:\n{research_brief}\n\n"
                    f"DRAFT:\n{draft}"
                ),
            }]
        },
        timings,
        trace=trace,
    )
    editor_verdict = last_text(editor_result)

    if trace:
        observability.print_run_summary(run_id, timings)

    return {
        "topic": topic,
        "research_brief": research_brief,
        "draft": draft,
        "editor_verdict": editor_verdict,
        "traces": {
            "researcher": research_result["messages"],
            "writer": write_result["messages"],
            "editor": editor_result["messages"],
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


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
