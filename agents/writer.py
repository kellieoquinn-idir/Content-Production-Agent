"""Writer agent: same create_agent pattern as weather_agent.py.

High temperature so the draft can be engaging. No tools — it writes
from the research brief the orchestrator will pass in later.
"""

from langchain.agents import create_agent

from llm import make_model
from prompts import WRITER_SYSTEM_PROMPT


def build_writer_agent():
    model = make_model(temperature=0.9)
    return create_agent(
        model,
        tools=[],
        system_prompt=WRITER_SYSTEM_PROMPT,
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
