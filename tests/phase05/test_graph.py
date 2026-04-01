"""
Phase 5 — AGENT-05 tests.
Verifies: LangGraph graph structure and self-correction retry loop.

All LLM and DB calls are mocked — no real API keys or containers needed.
"""
from unittest.mock import MagicMock, patch

import pytest

from src.agent.graph import NODE_EXECUTE, NODE_GENERATE, build_graph
from src.agent.state import AgentState


def _mock_llm(sql_responses: list[str]):
    """Return a mock get_llm that yields successive SQL strings."""
    responses = iter(sql_responses)

    def make_llm():
        mock_response = MagicMock()
        mock_response.content = next(responses, sql_responses[-1])
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response
        return mock_llm

    return make_llm


# ── Graph compilation ─────────────────────────────────────────────────────────

def test_build_graph_returns_compiled_graph():
    """AGENT-05: build_graph() returns a compiled LangGraph runnable."""
    graph = build_graph()
    assert hasattr(graph, "invoke")


def test_graph_has_expected_nodes():
    """AGENT-05: Graph contains generate_sql and execute_sql nodes."""
    graph = build_graph()
    node_names = set(graph.get_graph().nodes.keys())
    assert NODE_GENERATE in node_names
    assert NODE_EXECUTE in node_names


# ── Happy path ────────────────────────────────────────────────────────────────

@patch("src.agent.nodes.executor.execute_query")
@patch("src.agent.nodes.executor.get_sales_engine")
@patch("src.agent.nodes.sql_generator.get_llm")
def test_graph_succeeds_on_first_attempt(mock_get_llm, mock_engine, mock_exec):
    """AGENT-05: Graph completes without retrying when SQL runs cleanly."""
    mock_get_llm.return_value = _mock_llm(["SELECT COUNT(*) FROM customers"])()
    mock_exec.return_value = [{"count": 42}]

    graph = build_graph()
    result = graph.invoke({
        "question": "How many customers?",
        "schema": "Table: customers\n  id INTEGER",
        "db_targets": ["sales_db"],
    })

    assert result["error"] is None
    assert result["result"] == [{"count": 42}]
    assert mock_exec.call_count == 1   # executed once, no retry


# ── Self-correction loop ──────────────────────────────────────────────────────

@patch("src.agent.nodes.executor.execute_query")
@patch("src.agent.nodes.executor.get_sales_engine")
@patch("src.agent.nodes.sql_generator.get_llm")
def test_graph_retries_on_error_and_succeeds(mock_get_llm, mock_engine, mock_exec):
    """AGENT-05: Graph retries after one failure and succeeds on second attempt."""
    # First call raises, second call returns rows
    mock_exec.side_effect = [
        Exception("syntax error near 'SELCT'"),
        [{"id": 1}],
    ]
    # LLM returns bad SQL first, then corrected SQL
    call_count = {"n": 0}
    def make_llm():
        call_count["n"] += 1
        sql = "SELCT id FROM customers" if call_count["n"] == 1 else "SELECT id FROM customers"
        mock_response = MagicMock()
        mock_response.content = sql
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response
        return mock_llm
    mock_get_llm.side_effect = make_llm

    graph = build_graph()
    result = graph.invoke({
        "question": "List customers",
        "schema": "Table: customers\n  id INTEGER",
        "db_targets": ["sales_db"],
        "retry_count": 0,
    })

    assert result["result"] == [{"id": 1}]
    assert result["error"] is None
    assert mock_exec.call_count == 2


@patch("src.agent.nodes.executor.execute_query")
@patch("src.agent.nodes.executor.get_sales_engine")
@patch("src.agent.nodes.sql_generator.get_llm")
def test_graph_stops_after_max_retries(mock_get_llm, mock_engine, mock_exec):
    """AGENT-05: Graph stops and surfaces error after 3 retries."""
    mock_exec.side_effect = Exception("persistent error")

    mock_response = MagicMock()
    mock_response.content = "SELECT bad"
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm

    graph = build_graph()
    result = graph.invoke({
        "question": "Q",
        "schema": "Table: customers\n  id INTEGER",
        "db_targets": ["sales_db"],
        "retry_count": 0,
    })

    # After 3 failures retry_count should be 3 and error should be set
    assert result.get("error") is not None
    assert result.get("retry_count") == 3
    # Executor was called exactly 3 times (initial + 2 retries, stopped at 3)
    assert mock_exec.call_count == 3
