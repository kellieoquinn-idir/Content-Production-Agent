"""Load system prompts from Prompt Engineer's prompts.py when it exists.

Integration does not own prompt wording. When that file is added on the
prompts branch, these names are used automatically:

    RESEARCHER_SYSTEM_PROMPT
    WRITER_SYSTEM_PROMPT
    EDITOR_SYSTEM_PROMPT
"""

from importlib import import_module

_FALLBACKS = {
    "RESEARCHER_SYSTEM_PROMPT": (
        "You are the Fieldstone Media researcher agent. "
        "Call search_sources before writing the brief. "
        "Use only facts and URLs returned by that tool. Do not invent citations."
    ),
    "WRITER_SYSTEM_PROMPT": (
        "You are the Fieldstone Media writer agent. "
        "Prompt Engineer owns the full system prompt."
    ),
    "EDITOR_SYSTEM_PROMPT": (
        "You are the Fieldstone Media editor agent. "
        "Prompt Engineer owns the full system prompt."
    ),
}


def get_system_prompt(name: str, override: str | None = None) -> str:
    if override:
        return override
    try:
        prompts = import_module("prompts")
    except ImportError:
        return _FALLBACKS[name]
    return getattr(prompts, name, _FALLBACKS[name])
