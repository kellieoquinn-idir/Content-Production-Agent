"""Observability for the Fieldstone pipeline: full agent-exchange logging.

For each agent invocation (researcher / writer / editor), this module:
  - prints a readable trace of the full conversation (for `--trace` demos)
  - appends one JSON line per agent run to observability_log.jsonl
    (full message exchange, for later playback / debugging)
  - appends one JSON line per agent run to pipeline_metrics.jsonl
    (duration, message count, tool-call count, for timing analysis)

Both files are append-only and gitignored; each entry is tagged with a
run_id so multiple demo runs don't get mixed together.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path("observability_log.jsonl")
METRICS_PATH = Path("pipeline_metrics.jsonl")

_PREVIEW_LIMIT = 400


def new_run_id() -> str:
    return f"run-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stringify(content) -> str:
    return content if isinstance(content, str) else str(content)


def _truncate(text: str, limit: int = _PREVIEW_LIMIT) -> str:
    text = _stringify(text)
    return text if len(text) <= limit else text[:limit] + "..."


def _message_to_dict(message) -> dict:
    entry = {"type": type(message).__name__, "content": _stringify(message.content)}
    tool_calls = getattr(message, "tool_calls", None)
    if tool_calls:
        entry["tool_calls"] = [{"name": tc["name"], "args": tc["args"]} for tc in tool_calls]
    return entry


def print_agent_trace(agent_name: str, messages, duration_s: float) -> None:
    """Print a compact exchange for one agent (--trace demo output).

    Does not reprint full handoff payloads (topic / brief / draft). Those
    already appear in the pipeline output. JSONL still stores the full text.
    """
    print(f"\n{'=' * 60}")
    print(f"[{agent_name.upper()}] exchange ({duration_s:.2f}s)")
    print("=" * 60)
    for message in messages:
        entry = _message_to_dict(message)
        if entry.get("tool_calls"):
            for tc in entry["tool_calls"]:
                print(f"  [{entry['type']}] tool call -> {tc['name']}({tc['args']})")
        elif entry["type"] == "ToolMessage":
            print(f"  [{entry['type']}] result: {_truncate(entry['content'], 160)}")
        elif entry["type"] == "HumanMessage":
            n = len(entry["content"])
            print(f"  [{entry['type']}] handoff in ({n} chars)")
        else:
            print(f"  [{entry['type']}] {_truncate(entry['content'], 160)}")


def record_agent_run(run_id: str, agent_name: str, messages, duration_s: float) -> None:
    """Persist the full exchange and timing metrics for one agent invocation."""
    message_dicts = [_message_to_dict(m) for m in messages]
    tool_call_count = sum(len(m.get("tool_calls", [])) for m in message_dicts)

    log_entry = {
        "run_id": run_id,
        "agent": agent_name,
        "logged_at": _now(),
        "duration_s": round(duration_s, 3),
        "messages": message_dicts,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

    metric_entry = {
        "run_id": run_id,
        "agent": agent_name,
        "logged_at": _now(),
        "duration_s": round(duration_s, 3),
        "message_count": len(message_dicts),
        "tool_call_count": tool_call_count,
    }
    with METRICS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(metric_entry) + "\n")


def print_run_summary(run_id: str, timings: dict) -> None:
    print(f"\n{'=' * 60}")
    print(f"RUN SUMMARY ({run_id})")
    print("=" * 60)
    for agent_name, duration_s in timings.items():
        print(f"  {agent_name:<12} {duration_s:>6.2f}s")
    print(f"  {'total':<12} {sum(timings.values()):>6.2f}s")
