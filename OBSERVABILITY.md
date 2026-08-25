# Observability

`observability.py` records what each agent did during a pipeline run —
the full message exchange (including tool calls) and how long each agent
took. It's the piece that makes `python pipeline.py --trace` show a
readable, agent-by-agent account of a run instead of a wall of raw
message objects, and it leaves a permanent record behind for later
debugging.

This module doesn't call agents itself. It's wired in by whoever owns
the calling code (currently `pipeline.py`'s `run_pipeline()`) around
each `agent.invoke(...)` call.

## What it produces

Three things per agent invocation:

1. **A live terminal trace** — printed immediately, for demos.
2. **A JSONL log entry** in `observability_log.jsonl` — the full
   conversation (every message, every tool call and its result),
   for replaying or debugging a run after the fact.
3. **A JSONL metrics entry** in `pipeline_metrics.jsonl` — just the
   numbers (duration, message count, tool-call count), for timing
   analysis without having to parse full transcripts.

Both `.jsonl` files are append-only and gitignored — every run adds to
them rather than overwriting, and each entry is tagged with a `run_id`
so multiple runs (or a whole demo session) don't get mixed together.

## API

```python
import observability

run_id = observability.new_run_id()
# "run-20260824T234633541236"
```

Call once per pipeline run, before invoking any agents.

```python
observability.record_agent_run(run_id, agent_name, messages, duration_s)
```

Call once per agent invocation, after it returns. `messages` is the
`result["messages"]` list from a LangChain/`create_agent` result
(anything with `.content` and, on AI messages, `.tool_calls`).
Appends one line to `observability_log.jsonl` and one to
`pipeline_metrics.jsonl`.

```python
observability.print_agent_trace(agent_name, messages, duration_s)
```

Prints that same exchange to the terminal — only call this when the
caller actually wants trace output (e.g. `--trace` was passed), since
it's meant for demos, not silent runs.

```python
observability.print_run_summary(run_id, timings)
```

Prints a total-timing recap at the end of a run. `timings` is a dict
of `{agent_name: duration_s}`.

## Wiring it into a pipeline step

The intended pattern — time the call, then hand the result to both
functions:

```python
import time
import observability

run_id = observability.new_run_id()
timings = {}

started = time.perf_counter()
result = researcher.invoke({"messages": [...]})
duration_s = time.perf_counter() - started

timings["researcher"] = duration_s
observability.record_agent_run(run_id, "researcher", result["messages"], duration_s)
if trace_enabled:
    observability.print_agent_trace("researcher", result["messages"], duration_s)

# ...repeat per agent, then at the end:
if trace_enabled:
    observability.print_run_summary(run_id, timings)
```

Logging to the JSONL files (`record_agent_run`) is cheap and safe to
call on every run, trace or not — it's the terminal printing
(`print_agent_trace` / `print_run_summary`) that should stay gated
behind whatever flag controls demo output, so a normal run isn't noisy.

## Log formats

`observability_log.jsonl` — one line per agent invocation:

```json
{
  "run_id": "run-20260824T234633541236",
  "agent": "researcher",
  "logged_at": "2026-08-24T23:46:33.542902+00:00",
  "duration_s": 4.912,
  "messages": [
    {"type": "HumanMessage", "content": "Research this travel blog topic: ..."},
    {"type": "AIMessage", "content": "", "tool_calls": [{"name": "search_sources", "args": {"topic": "Lisbon"}}]},
    {"type": "ToolMessage", "content": "1. Source A\n   Fact: ...\n   Citation: http://..."},
    {"type": "AIMessage", "content": "RESEARCH BRIEF: ..."}
  ]
}
```

`pipeline_metrics.jsonl` — one line per agent invocation, numbers only:

```json
{
  "run_id": "run-20260824T234633541236",
  "agent": "researcher",
  "logged_at": "2026-08-24T23:46:33.543345+00:00",
  "duration_s": 4.912,
  "message_count": 4,
  "tool_call_count": 1
}
```

To pull up everything from one run:

```bash
grep '"run-20260824T234633541236"' observability_log.jsonl
```

## Ownership

Darnel owns this file and the log formats it writes. Changing what gets
logged, or adding new fields, happens here — the calling code (pipeline
or orchestrator) just passes in `agent_name`, `messages`, and
`duration_s`.
