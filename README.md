# Content Production Agent

## Scenario
Fieldstone Media is a content production agency specializing in travel blogging to increase tourism in client locations.  
Current workflow:
- Researcher gathers credible sources into a shared doc  
- Writer drafts from those sources to create an engaging blog with the focus of increasing tourism to the location written about. 
- Editor fact-checks line by line before publishing and reviews for readability, grammar, tone, etc. 
A 3-day blog post, run in one command.

Fieldstone already ships well-researched, well-written posts. The bottleneck is **time**: researcher → writer → editor, all in sequence, all billable. This prototype keeps that same chain (and the editor’s veto) but has agents do the slow parts.

```
topic
  → researcher  (search + cited brief)
  → writer      (draft from the brief only)
  → editor      (PASS or REVISE)
```

## Run it

Python 3.10+ (3.12 is what we use). DeepSeek key from class.

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

`--trace` prints the full agent exchange (for the demo / observability).

## Who does what


| File                   | Job                                     |
| ---------------------- | --------------------------------------- |
| `agents/researcher.py` | Finds sources, writes a cited brief     |
| `agents/writer.py`     | Turns the brief into a ≥300 word post   |
| `agents/editor.py`     | Fact-checks the draft against the brief |
| `tools.py`             | Live web search (`search_sources`)      |
| `pipeline.py`          | Hands the folder from desk to desk      |
| `llm.py`               | Shared DeepSeek setup                   |

