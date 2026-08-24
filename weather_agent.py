"""Step 1 smoke test: the class create_agent + DeepSeek weather example.

This is the same agent from agentic_simple_langchain_deepseek_demo.ipynb.
If this script runs, the LangChain + DeepSeek setup works and we can
build the Fieldstone researcher / writer / editor agents on top of it.
"""

import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_deepseek import ChatDeepSeek

load_dotenv()  # reads DEEPSEEK_API_KEY from a .env file in this directory


# ---------------------------------------------------------------------------
# 1. DEFINE THE TOOL
#    Same as the manual-loop version: the @tool decorator turns this into a
#    LangChain tool, and the docstring becomes the description the model
#    sees and uses to decide when to call it.
# ---------------------------------------------------------------------------

@tool
def get_weather(city: str) -> str:
    """Get weather of a state, county, or city, specifically in the United
    States of America. The input should be a city name, for example:
    'New York City' or 'Atlanta'."""
    current_city = city.lower()
    fake_cities = {"new york": "58 degrees", "atlanta": "60 degrees"}
    return fake_cities.get(current_city, f"No weather data available for '{city}'.")


# ---------------------------------------------------------------------------
# 2. SET UP THE MODEL
#    Note: unlike the manual-loop version, we do NOT call .bind_tools() here.
#    create_agent takes the raw model and the tool list separately and wires
#    them together itself.
# ---------------------------------------------------------------------------

model = ChatDeepSeek(
    model="deepseek-v4-flash",
    temperature=0,
)


# ---------------------------------------------------------------------------
# 3. BUILD THE AGENT
#    This single call replaces the entire loop, tool-call detection, and
#    result-feeding logic from the manual-loop version. Internally it builds
#    a small LangGraph graph (model node + tools node) and runs it until the
#    model produces a final answer.
# ---------------------------------------------------------------------------

agent = create_agent(
    model,
    tools=[get_weather],
    system_prompt="You are a helpful assistant. Be concise and accurate.",
)


# ---------------------------------------------------------------------------
# 4. INSPECT WHAT HAPPENED
#    Even though create_agent runs the loop internally, every step is still
#    visible afterward in the returned message list -- the tool call and
#    tool result are all there, same as if we'd logged them ourselves.
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# 5. RUN IT
#    No for loop, no max_steps guard to write, no manual tool-call handling.
#    agent.invoke(...) runs the full loop and returns once the model gives
#    a final answer.
# ---------------------------------------------------------------------------

def main():
    if not os.getenv("DEEPSEEK_API_KEY"):
        raise SystemExit(
            "Missing DEEPSEEK_API_KEY. Copy .env.example to .env and paste your class key."
        )

    user_input = "How's the weather in Atlanta, Georgia?"
    print(f"User>\t {user_input}")

    result = agent.invoke({
        "messages": [{"role": "user", "content": user_input}]
    })

    print(f"Model>\t {result['messages'][-1].content}")
    print("\n--- Full trace ---")
    print_trace(result["messages"])


if __name__ == "__main__":
    main()
