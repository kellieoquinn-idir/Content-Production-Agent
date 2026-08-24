"""Researcher agent: same create_agent pattern as weather_agent.py.

Low temperature. Search tool comes in the next integration step.
System prompt comes from Prompt Engineer (prompts.py) when it exists.
"""

from langchain.agents import create_agent

from agents.prompt_source import get_system_prompt
from llm import make_model


def build_researcher_agent(system_prompt: str | None = None):
    model = make_model(temperature=0)
    return create_agent(
        model,
        tools=[],
        system_prompt=get_system_prompt("RESEARCHER_SYSTEM_PROMPT", system_prompt),
        name="researcher",
    )


def main():
    topic = "best time to visit Lisbon"
    agent = build_researcher_agent()
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": f"Research this travel blog topic: {topic}",
        }]
    })
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
