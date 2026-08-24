"""Editor agent: same create_agent pattern as weather_agent.py.

Low-ish temperature so fact-checking stays strict. No tools — it
compares the draft to the research brief the orchestrator will pass in.
System prompt comes from Prompt Engineer (prompts.py) when it exists.
"""

from langchain.agents import create_agent

from agents.prompt_source import get_system_prompt
from llm import make_model


def build_editor_agent(system_prompt: str | None = None):
    model = make_model(temperature=0.2)
    return create_agent(
        model,
        tools=[],
        system_prompt=get_system_prompt("EDITOR_SYSTEM_PROMPT", system_prompt),
        name="editor",
    )


def main():
    agent = build_editor_agent()
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": (
                "Review this draft against the research brief.\n\n"
                "RESEARCH BRIEF:\n(none yet)\n\n"
                "DRAFT:\n(none yet)\n\n"
                "Say PASS or REVISE."
            ),
        }]
    })
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
