"""Researcher agent: same create_agent pattern as weather_agent.py.

Low temperature. Search tool comes in the next integration step.
"""

from langchain.agents import create_agent

from llm import make_model
from prompts import RESEARCHER_SYSTEM_PROMPT


def build_researcher_agent():
    model = make_model(temperature=0)
    return create_agent(
        model,
        tools=[],
        system_prompt=RESEARCHER_SYSTEM_PROMPT,
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
