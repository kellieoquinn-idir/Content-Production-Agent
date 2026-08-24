"""Editor agent: same create_agent pattern as weather_agent.py.

Low-ish temperature so fact-checking stays strict. No tools — it
compares the draft to the research brief the orchestrator will pass in.
"""

from langchain.agents import create_agent

from llm import make_model
from prompts import EDITOR_SYSTEM_PROMPT


def build_editor_agent():
    model = make_model(temperature=0.2)
    return create_agent(
        model,
        tools=[],
        system_prompt=EDITOR_SYSTEM_PROMPT,
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
