"""Researcher agent: same create_agent pattern as weather_agent.py.

Low temperature. Uses the search_sources tool (stub catalog for now).
System prompt comes from Prompt Engineer (prompts.py) when it exists.
"""

from langchain.agents import create_agent

from agents.prompt_source import get_system_prompt
from llm import make_model
from tools import search_sources


def build_researcher_agent(system_prompt: str | None = None):
    model = make_model(temperature=0)
    return create_agent(
        model,
        tools=[search_sources],
        system_prompt=get_system_prompt("RESEARCHER_SYSTEM_PROMPT", system_prompt),
        name="researcher",
    )


def print_trace(messages):
    for message in messages:
        label = type(message).__name__
        if getattr(message, "tool_calls", None):
            for tc in message.tool_calls:
                print(f"[{label}] requested tool call: {tc['name']}({tc['args']})")
        elif label == "ToolMessage":
            print(f"[{label}] result: {message.content}")
        else:
            print(f"[{label}] {message.content}")


def main():
    topic = "best time to visit Lisbon"
    agent = build_researcher_agent()
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": (
                f"Research this travel blog topic: {topic}. "
                "Use the search_sources tool. Produce a brief with at least "
                "5 facts and citations from the tool results."
            ),
        }]
    })
    print(result["messages"][-1].content)
    print("\n--- Full trace ---")
    print_trace(result["messages"])


if __name__ == "__main__":
    main()
