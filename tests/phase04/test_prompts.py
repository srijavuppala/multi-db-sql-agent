"""
Phase 4 — AGENT-02 tests.
Verifies: prompt builder output structure and content.
"""
from langchain_core.messages import HumanMessage, SystemMessage

from src.agent.prompts import (
    build_sql_correction_prompt,
    build_sql_generation_prompt,
)

_SCHEMA = "Table: customers\n  id INTEGER\n  name TEXT NOT NULL"


def test_generation_prompt_returns_two_messages():
    """AGENT-02: build_sql_generation_prompt returns [SystemMessage, HumanMessage]."""
    msgs = build_sql_generation_prompt(
        question="How many customers?",
        schema=_SCHEMA,
        db_targets=["sales_db"],
    )
    assert len(msgs) == 2
    assert isinstance(msgs[0], SystemMessage)
    assert isinstance(msgs[1], HumanMessage)


def test_generation_prompt_contains_question():
    """AGENT-02: Human message contains the original question."""
    msgs = build_sql_generation_prompt(
        question="List all cities",
        schema=_SCHEMA,
        db_targets=["sales_db"],
    )
    assert "List all cities" in msgs[1].content


def test_generation_prompt_contains_schema():
    """AGENT-02: Human message contains the schema."""
    msgs = build_sql_generation_prompt(
        question="How many customers?",
        schema=_SCHEMA,
        db_targets=["sales_db"],
    )
    assert "customers" in msgs[1].content
    assert "INTEGER" in msgs[1].content


def test_generation_prompt_contains_db_label():
    """AGENT-02: Human message mentions the target database."""
    msgs = build_sql_generation_prompt(
        question="Q?",
        schema=_SCHEMA,
        db_targets=["sales_db"],
    )
    assert "sales_db" in msgs[1].content


def test_correction_prompt_contains_error():
    """AGENT-02: Correction prompt includes the error message."""
    msgs = build_sql_correction_prompt(
        question="How many?",
        schema=_SCHEMA,
        sql="SELCT * FROM customers",
        error="syntax error at or near 'SELCT'",
    )
    assert "syntax error" in msgs[1].content


def test_correction_prompt_contains_bad_sql():
    """AGENT-02: Correction prompt includes the failing SQL."""
    msgs = build_sql_correction_prompt(
        question="How many?",
        schema=_SCHEMA,
        sql="SELCT * FROM customers",
        error="syntax error",
    )
    assert "SELCT" in msgs[1].content


def test_system_prompt_forbids_mutations():
    """AGENT-02: System prompt instructs the LLM not to write mutations."""
    msgs = build_sql_generation_prompt("Q?", _SCHEMA, ["sales_db"])
    system_content = msgs[0].content
    assert "SELECT" in system_content
    assert "INSERT" in system_content or "never" in system_content.lower()
