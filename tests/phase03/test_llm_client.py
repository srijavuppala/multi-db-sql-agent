"""
Phase 3 — LLM-03 tests.
Verifies: get_llm() factory behaviour without making real API calls.
"""
import os
import pytest


def test_get_llm_raises_without_api_key(monkeypatch):
    """LLM-03: get_llm() raises ValueError when ANTHROPIC_API_KEY is absent."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")

    from src.llm.client import get_llm

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        get_llm()


def test_get_llm_raises_for_unknown_provider(monkeypatch):
    """LLM-03: get_llm() raises ValueError for an unrecognised provider."""
    monkeypatch.setenv("LLM_PROVIDER", "cohere")

    from src.llm.client import get_llm

    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
        get_llm(provider="cohere")


def test_get_llm_anthropic_returns_chat_model(monkeypatch):
    """LLM-03: get_llm() with a fake API key returns a BaseChatModel instance."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake-key-for-testing")
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")

    from langchain_core.language_models import BaseChatModel
    from src.llm.client import get_llm

    llm = get_llm()
    assert isinstance(llm, BaseChatModel)


def test_get_llm_openai_raises_without_api_key(monkeypatch):
    """LLM-03: get_llm(provider='openai') raises ValueError when key is absent."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from src.llm.client import get_llm

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        get_llm(provider="openai")


def test_get_llm_provider_env_var_respected(monkeypatch):
    """LLM-03: LLM_PROVIDER env var is used when no explicit provider is given."""
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake-key-for-testing")

    from src.llm.client import get_llm

    llm = get_llm()
    # ChatAnthropic stores the model name as .model
    assert hasattr(llm, "model")


def test_get_llm_model_override(monkeypatch):
    """LLM-03: Explicit model argument overrides the default."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake-key-for-testing")

    from src.llm.client import get_llm

    llm = get_llm(provider="anthropic", model="claude-haiku-4-5-20251001")
    assert "haiku" in llm.model.lower()
