"""Shared DeepSeek model setup for every Fieldstone agent."""

import os

from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek

load_dotenv()

MODEL_NAME = "deepseek-v4-flash"


def require_api_key() -> None:
    if not os.getenv("DEEPSEEK_API_KEY"):
        raise SystemExit(
            "Missing DEEPSEEK_API_KEY. Copy .env.example to .env and paste your class key."
        )


def make_model(temperature: float) -> ChatDeepSeek:
    require_api_key()
    return ChatDeepSeek(model=MODEL_NAME, temperature=temperature)
