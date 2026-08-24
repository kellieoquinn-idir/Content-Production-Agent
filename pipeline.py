"""Sequential Fieldstone pipeline: researcher → writer → editor.

Integration owns this handoff. Jared's orchestrator can call run_pipeline()
later for parallel start / routing. Ayoka owns retry rules; this file does
one editor pass and stops.

Handoff shape:
    topic: str
    research_brief: str   # researcher final text, ≥5 cited facts
    draft: str            # writer final text, ≥300 words
    editor_verdict: str   # editor final text, should include PASS or REVISE
    traces: dict          # each invoke's messages, for Darnel
"""

import argparse
import sys

from agents.editor import build_editor_agent
from agents.researcher import build_researcher_agent
from agents.writer import build_writer_agent
from llm import require_api_key


def last_text(result) -> str:
    content = result["messages"][-1].content
    if isinstance(content, str):
        return content
    return str(content)


def print_trace(messages) -> None:
    for message in messages:
        label = type(message).__name__
        if getattr(message, "tool_calls", None):
            for tc in message.tool_calls:
                print(f"[{label}] requested tool call: {tc['name']}({tc['args']})")
        elif label == "ToolMessage":
            preview = message.content if len(str(message.content)) < 400 else str(message.content)[:400] + "..."
            print(f"[{label}] result: {preview}")
        else:
            preview = message.content if len(str(message.content)) < 400 else str(message.content)[:400] + "..."
            print(f"[{label}] {preview}")


def run_pipeline(topic: str) -> dict:
    require_api_key()

    researcher = build_researcher_agent()
    writer = build_writer_agent()
    editor = build_editor_agent()

    research_result = researcher.invoke({
        "messages": [{
            "role": "user",
            "content": (
                f"Research this travel blog topic: {topic}. "
                "Use the search_sources tool. Produce a brief with at least "
                "5 facts and citations from the tool results."
            ),
        }]
    })
    research_brief = last_text(research_result)

    write_result = writer.invoke({
        "messages": [{
            "role": "user",
            "content": (
                f"Write a travel blog post about: {topic}\n\n"
                "Use only the research brief below. Do not invent facts.\n\n"
                f"RESEARCH BRIEF:\n{research_brief}"
            ),
        }]
    })
    draft = last_text(write_result)

    editor_result = editor.invoke({
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
    })
    editor_verdict = last_text(editor_result)

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
    result = run_pipeline(args.topic)

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

    if args.trace:
        print()
        print("=" * 60)
        print("TRACES")
        print("=" * 60)
        for name, messages in result["traces"].items():
            print(f"\n--- {name} ---")
            print_trace(messages)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
