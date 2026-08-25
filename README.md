# Content Production Agent

A 3-day blog post, run in one command.

Fieldstone already ships well-researched, well-written posts. The bottleneck is **time**: researcher → writer → editor, all in sequence, all billable. This prototype keeps that same chain (and the editor’s veto) but has agents do the slow parts.

```
topic
  → researcher  (search + cited brief)
  → writer      (draft from the brief only)
  → editor      (PASS or REVISE)
       ↺ first REVISE: writer fixes from editor notes
       → second REVISE: flag a human editor (this is the checkpoint that stays)
```

## Run it

Python 3.10+ (3.12 is what we use).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # paste DEEPSEEK_API_KEY
python pipeline.py
```

Try another topic:

```bash
python pipeline.py "hiking in Patagonia"
python pipeline.py "best time to visit Lisbon" --trace
```

`--trace` prints the full agent exchange (Darnel's observability). Every run also appends to `observability_log.jsonl` and `pipeline_metrics.jsonl` (gitignored).

## Who does what


| File                   | Job                                     |
| ---------------------- | --------------------------------------- |
| `agents/researcher.py` | Finds sources, writes a cited brief     |
| `agents/writer.py`     | Turns the brief into a ≥300 word post   |
| `agents/editor.py`     | Fact-checks the draft against the brief |
| `tools.py`             | Live web search (`search_sources`)      |
| `critic.py`             | PASS vs REVISE rules and retry limit   |
| `pipeline.py`           | Hands work desk to desk, runs retries  |
| `orchestrator/`         | Manager that calls the pipeline        |
| `main.py`               | Type a topic and run the full system   |
| `llm.py`                | Shared DeepSeek setup                  |

