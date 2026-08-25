"""Critic rules and retry policy (Ayoka's part).

The editor agent still writes the review. This module decides what PASS vs
REVISE means, applies hard checks the LLM might skip, and caps retries.
"""

REVISE_LIMIT = 2  # two REVISE verdicts → flag a human editor
MAX_RETRIES = 1   # one writer rewrite between those two reviews
MIN_DRAFT_WORDS = 300

EDITOR_CHECKLIST = """
Pass/revise rules (apply all of them):
1. First line of your response must be exactly PASS or REVISE.
2. Every factual claim in the draft must be supported by the research brief.
   Invented facts, extra statistics, or unsourced specifics = REVISE.
3. The draft must be at least 300 words. Shorter = REVISE.
4. Weak, vague, or unreadable sections = REVISE, with specific fix notes.
5. PASS only if 2–4 all hold. Do not PASS to be nice.
6. If REVISE, list numbered issues the writer must fix. Do not rewrite the
   whole post yourself.
""".strip()


def word_count(text: str) -> int:
    return len(text.split())


def parse_decision(verdict: str) -> str:
    """Read PASS / REVISE from the top of the editor's response."""
    if not verdict or not str(verdict).strip():
        return "UNKNOWN"

    head = str(verdict).strip().upper()
    first_line = head.splitlines()[0]
    # Prefer the first line so a later "if you revise..." doesn't flip PASS.
    if first_line.startswith("REVISE") or first_line == "REVISE":
        return "REVISE"
    if first_line.startswith("PASS") or first_line == "PASS":
        return "PASS"
    if "REVISE" in head[:400]:
        return "REVISE"
    if "PASS" in head[:400]:
        return "PASS"
    return "UNKNOWN"


def hard_fail_reasons(draft: str) -> list[str]:
    """Programmatic checks. These can override a too-generous PASS."""
    reasons = []
    n = word_count(draft)
    if n < MIN_DRAFT_WORDS:
        reasons.append(
            f"Draft is {n} words; it must be at least {MIN_DRAFT_WORDS}."
        )
    return reasons


def apply_critic(verdict: str, draft: str) -> tuple[str, str]:
    """Combine editor verdict with hard checks.

    If the editor PASSes but a hard rule fails, decision becomes REVISE
    (critic and writer/editor disagree — critic wins).
    """
    decision = parse_decision(verdict)
    forced = hard_fail_reasons(draft)
    if forced:
        notes = "Hard critic checks failed:\n" + "\n".join(f"- {r}" for r in forced)
        if decision == "PASS":
            combined = (
                "REVISE\n\nThe editor passed this draft, but the critic "
                "rejected it.\n\n" + notes
            )
            return "REVISE", combined
        return "REVISE", str(verdict).rstrip() + "\n\n" + notes
    if decision == "UNKNOWN":
        return "UNKNOWN", verdict
    return decision, verdict
