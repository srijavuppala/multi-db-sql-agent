"""
Phase 4 — AGENT-03 tests.
Verifies: sql_generation_node behaviour using a mocked LLM.

All tests mock the LLM so no real API key or network call is needed.
"""
from unittest.mock import MagicMock, patch

import pytest

from src.agent.nodes.sql_generator import _extract_sql, sql_generation_node
from src.agent.state import AgentState


# ── _extract_sql unit tests ───────────────────────────────────────────────────

def test_extract_sql_strips_sql_fence():
    """AGENT-03: SQL wrapped in ```sql ... ``` is extracted cleanly."""
    raw = "```sql\nSELECT * FROM customers\n```"
    assert _extract_sql(raw) == "SELECT * FROM customers"


def test_extract_sql_strips_plain_fence():
    """AGENT-03: SQL wrapped in plain ``` ... ``` is extracted cleanly."""
    raw = "```\nSELECT id FROM orders\n```"
    assert _extract_sql(raw) == "SELECT id FROM orders"


def test_extract_sql_passthrough_no_fence():
    """AGENT-03: SQL without fences is returned as-is (stripped)."""
    raw = "  SELECT id FROM orders  "
    assert _extract_sql(raw) == "SELECT id FROM orders"


def test_extract_sql_multiline():
    """AGENT-03: Multi-line SQL inside a fence is preserved."""
    raw = "```sql\nSELECT id,\n  name\nFROM customers\n```"
    result = _extract_sql(raw)
    assert "SELECT id," in result
    assert "FROM customers" in result


# ── sql_generation_node integration tests (mocked LLM) ───────────────────────

def _make_mock_llm(response_text: str):
    mock_response = MagicMock()
    mock_response.content = response_text
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_response
    return mock_llm


@patch("src.agent.nodes.sql_generator.get_llm")
def test_node_returns_sql_patch(mock_get_llm):
    """AGENT-03: Node returns a dict with 'sql' key."""
    mock_get_llm.return_value = _make_mock_llm("SELECT COUNT(*) FROM customers")

    state: AgentState = {
        "question": "How many customers?",
        "schema": "Table: customers\n  id INTEGER",
        "db_targets": ["sales_db"],
    }
    result = sql_generation_node(state)

    assert "sql" in result
    assert "SELECT" in result["sql"].upper()


@patch("src.agent.nodes.sql_generator.get_llm")
def test_node_strips_fences_from_llm_output(mock_get_llm):
    """AGENT-03: Node strips markdown fences before storing SQL."""
    mock_get_llm.return_value = _make_mock_llm(
        "```sql\nSELECT * FROM customers\n```"
    )

    state: AgentState = {
        "question": "List customers",
        "schema": "Table: customers\n  id INTEGER",
        "db_targets": ["sales_db"],
    }
    result = sql_generation_node(state)

    assert result["sql"] == "SELECT * FROM customers"
    assert "```" not in result["sql"]


@patch("src.agent.nodes.sql_generator.get_llm")
def test_node_uses_correction_prompt_when_error_present(mock_get_llm):
    """AGENT-03: Node calls correction prompt when state has an error."""
    mock_llm = _make_mock_llm("SELECT id FROM customers")
    mock_get_llm.return_value = mock_llm

    state: AgentState = {
        "question": "List customers",
        "schema": "Table: customers\n  id INTEGER",
        "db_targets": ["sales_db"],
        "sql": "SELCT id FROM customers",
        "error": "syntax error near 'SELCT'",
    }
    sql_generation_node(state)

    # LLM was called — verify the correction prompt content reached it
    call_args = mock_llm.invoke.call_args[0][0]  # first positional arg = messages
    human_content = call_args[1].content
    assert "syntax error" in human_content
    assert "SELCT" in human_content


@patch("src.agent.nodes.sql_generator.get_llm")
def test_node_uses_generation_prompt_when_no_error(mock_get_llm):
    """AGENT-03: Node calls generation prompt when state has no error."""
    mock_llm = _make_mock_llm("SELECT * FROM customers")
    mock_get_llm.return_value = mock_llm

    state: AgentState = {
        "question": "All customers?",
        "schema": "Table: customers\n  id INTEGER",
        "db_targets": ["sales_db"],
    }
    sql_generation_node(state)

    call_args = mock_llm.invoke.call_args[0][0]
    human_content = call_args[1].content
    assert "All customers?" in human_content


@patch("src.agent.nodes.sql_generator.get_llm")
def test_node_only_returns_sql_key(mock_get_llm):
    """AGENT-03: Node returns only {'sql': ...} — does not clobber other state."""
    mock_get_llm.return_value = _make_mock_llm("SELECT 1")

    state: AgentState = {
        "question": "Q",
        "schema": "Table: customers\n  id INTEGER",
        "db_targets": ["sales_db"],
        "retry_count": 2,
        "result": [{"id": 1}],
    }
    patch_dict = sql_generation_node(state)

    assert set(patch_dict.keys()) == {"sql"}
