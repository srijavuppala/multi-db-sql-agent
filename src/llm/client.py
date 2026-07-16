"""
LLM abstraction layer.

Returns a LangChain BaseChatModel backed by either Claude or OpenAI,
controlled by the LLM_PROVIDER env var (default: "anthropic").

Usage:
    from src.llm.client import get_llm

    llm = get_llm()                        # uses LLM_PROVIDER env var
    llm = get_llm(provider="openai")       # force OpenAI
    llm = get_llm(model="claude-opus-4-6") # override model

Environment variables:
    LLM_PROVIDER      — "anthropic" (default) or "openai"
    ANTHROPIC_API_KEY — required when provider is anthropic
    ANTHROPIC_MODEL   — default: claude-opus-4-6
    OPENAI_API_KEY    — required when provider is openai
    OPENAI_MODEL      — default: gpt-4o
"""
import os

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel

load_dotenv()

_DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-6"
_DEFAULT_OPENAI_MODEL = "gpt-4o"


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.0,
) -> BaseChatModel:
    """Return a LangChain chat model for the configured provider.

    Args:
        provider: "anthropic" or "openai". Defaults to LLM_PROVIDER env var,
                  then "anthropic".
        model:    Model name override. Defaults to ANTHROPIC_MODEL /
                  OPENAI_MODEL env vars, then sensible defaults.
        temperature: Sampling temperature (0.0 = deterministic SQL generation).

    Returns:
        A LangChain BaseChatModel instance (not yet connected — lazy init).

    Raises:
        ValueError: If provider is unknown or required API key is missing.
    """
    resolved_provider = (provider or os.getenv("LLM_PROVIDER", "anthropic")).lower()

    if resolved_provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. "
                "Add it to your .env file or environment."
            )
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model or os.getenv("ANTHROPIC_MODEL", _DEFAULT_ANTHROPIC_MODEL),
            api_key=api_key,
            temperature=temperature,
        )

    if resolved_provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. "
                "Add it to your .env file or environment."
            )
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model or os.getenv("OPENAI_MODEL", _DEFAULT_OPENAI_MODEL),
            api_key=api_key,
            temperature=temperature,
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER: {resolved_provider!r}. "
        "Valid values: 'anthropic', 'openai'."
    )
