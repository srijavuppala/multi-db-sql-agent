"""
Phase 5 — AGENT-05 tests.
Verifies: LangGraph graph structure and self-correction retry loop.

All LLM and DB calls are mocked — no real API keys or containers needed.
Note: graph structure tests reflect the full Phase 6 pipeline (router,
schema_inject, generate_sql, execute_sql, synthesize).
"""
from unittest.mock import MagicMock, patch

import pytest

from src.agent.graph import NODE_EXECUTE, NODE_GENERATE, build_graph
from src.agent.state import AgentState


def _mock_llm(sql: str):
    resp = MagicMock()
    resp.content = sql
    llm = MagicMock()
    llm.invoke.return_value = resp
    return llm


def _patch_schema():
    """Context: patch schema_injector so it doesn't touch real DBs."""
    return [
        patch("src.agent.nodes.schema_injector.get_sales_engine"),
        patch("src.agent.nodes.schema_injector.get_schema", return_value="Table: customers\n  id INTEGER"),
    ]


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

@patch("src.agent.nodes.synthesizer.get_llm")
@patch("src.agent.nodes.executor.execute_query")
@patch("src.agent.nodes.executor.get_sales_engine")
@patch("src.agent.nodes.schema_injector.get_schema")
@patch("src.agent.nodes.schema_injector.get_sales_engine")
@patch("src.agent.nodes.sql_generator.get_llm")
def test_graph_succeeds_on_first_attempt(
    mock_gen_llm, mock_schema_sales, mock_get_schema,
    mock_exec_sales, mock_exec_query, mock_synth_llm,
):
    """AGENT-05: Graph completes without retrying when SQL runs cleanly."""
    mock_gen_llm.return_value = _mock_llm("SELECT COUNT(*) FROM customers")
    mock_get_schema.return_value = "Table: customers\n  id INTEGER"
    mock_exec_query.return_value = [{"count": 42}]
    synth_resp = MagicMock()
    synth_resp.content = "There are 42 customers."
    mock_synth_llm.return_value = MagicMock(invoke=MagicMock(return_value=synth_resp))

    graph = build_graph()
    result = graph.invoke({"question": "How many customers?"})

    assert result["error"] is None
    assert result["result"] == [{"count": 42}]
    assert mock_exec_query.call_count == 1


# ── Self-correction loop ──────────────────────────────────────────────────────

@patch("src.agent.nodes.synthesizer.get_llm")
@patch("src.agent.nodes.executor.execute_query")
@patch("src.agent.nodes.executor.get_sales_engine")
@patch("src.agent.nodes.schema_injector.get_schema")
@patch("src.agent.nodes.schema_injector.get_sales_engine")
@patch("src.agent.nodes.sql_generator.get_llm")
def test_graph_retries_on_error_and_succeeds(
    mock_gen_llm, mock_schema_sales, mock_get_schema,
    mock_exec_sales, mock_exec_query, mock_synth_llm,
):
    """AGENT-05: Graph retries after one failure and succeeds on second attempt."""
    mock_exec_query.side_effect = [
        Exception("syntax error near 'SELCT'"),
        [{"id": 1}],
    ]
    mock_get_schema.return_value = "Table: customers\n  id INTEGER"
    call_count = {"n": 0}

    def make_llm():
        call_count["n"] += 1
        sql = "SELCT id FROM customers" if call_count["n"] == 1 else "SELECT id FROM customers"
        resp = MagicMock()
        resp.content = sql
        llm = MagicMock()
        llm.invoke.return_value = resp
        return llm

    mock_gen_llm.side_effect = make_llm
    synth_resp = MagicMock()
    synth_resp.content = "Found 1 customer."
    mock_synth_llm.return_value = MagicMock(invoke=MagicMock(return_value=synth_resp))

    graph = build_graph()
    result = graph.invoke({"question": "List customers", "retry_count": 0})

    assert result["result"] == [{"id": 1}]
    assert result["error"] is None
    assert mock_exec_query.call_count == 2


@patch("src.agent.nodes.synthesizer.get_llm")
@patch("src.agent.nodes.executor.execute_query")
@patch("src.agent.nodes.executor.get_sales_engine")
@patch("src.agent.nodes.schema_injector.get_schema")
@patch("src.agent.nodes.schema_injector.get_sales_engine")
@patch("src.agent.nodes.sql_generator.get_llm")
def test_graph_stops_after_max_retries(
    mock_gen_llm, mock_schema_sales, mock_get_schema,
    mock_exec_sales, mock_exec_query, mock_synth_llm,
):
    """AGENT-05: Graph stops and surfaces error after 3 retries."""
    mock_exec_query.side_effect = Exception("persistent error")
    mock_get_schema.return_value = "Table: customers\n  id INTEGER"

    resp = MagicMock()
    resp.content = "SELECT bad"
    llm = MagicMock()
    llm.invoke.return_value = resp
    mock_gen_llm.return_value = llm

    synth_resp = MagicMock()
    synth_resp.content = "Unable to answer."
    mock_synth_llm.return_value = MagicMock(invoke=MagicMock(return_value=synth_resp))

    graph = build_graph()
    result = graph.invoke({"question": "Q", "retry_count": 0})

    assert result.get("error") is not None
    assert result.get("retry_count") == 3
    assert mock_exec_query.call_count == 3
