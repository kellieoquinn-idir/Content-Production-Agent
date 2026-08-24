"""Writer agent: same create_agent pattern as weather_agent.py.

High temperature so the draft can be engaging. No tools — it writes
from the research brief the orchestrator will pass in later.
System prompt comes from Prompt Engineer (prompts.py) when it exists.
"""

from langchain.agents import create_agent

from agents.prompt_source import get_system_prompt
from llm import make_model


def build_writer_agent(system_prompt: str | None = None):
    model = make_model(temperature=0.9)
    return create_agent(
        model,
        tools=[],
        system_prompt=get_system_prompt("WRITER_SYSTEM_PROMPT", system_prompt),
        name="writer",
    )


def main():
    agent = build_writer_agent()
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": (
                "Write a travel blog post about Lisbon.\n\n"
                "Research brief: (none yet — outline from the topic only.)"
            ),
        }]
    })
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
