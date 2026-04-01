"""Phase 6 — AGENT-09: full graph pipeline tests (all external calls mocked)."""
from unittest.mock import MagicMock, patch

from src.agent.graph import (
    NODE_EXECUTE,
    NODE_GENERATE,
    NODE_ROUTER,
    NODE_SCHEMA,
    NODE_SYNTHESIZE,
    build_graph,
)


def _llm(text: str):
    resp = MagicMock()
    resp.content = text
    llm = MagicMock()
    llm.invoke.return_value = resp
    return llm


def test_graph_has_all_five_nodes():
    graph = build_graph()
    nodes = set(graph.get_graph().nodes.keys())
    assert {NODE_ROUTER, NODE_SCHEMA, NODE_GENERATE, NODE_EXECUTE, NODE_SYNTHESIZE}.issubset(nodes)


@patch("src.agent.nodes.synthesizer.get_llm")
@patch("src.agent.nodes.executor.execute_query")
@patch("src.agent.nodes.executor.get_sales_engine")
@patch("src.agent.nodes.schema_injector.get_schema")
@patch("src.agent.nodes.schema_injector.get_sales_engine")
@patch("src.agent.nodes.sql_generator.get_llm")
def test_full_pipeline_sales_question(
    mock_gen_llm, mock_schema_sales, mock_get_schema,
    mock_exec_sales, mock_exec_query, mock_synth_llm,
):
    mock_gen_llm.return_value = _llm("SELECT COUNT(*) FROM customers")
    mock_get_schema.return_value = "Table: customers\n  id INTEGER"
    mock_exec_query.return_value = [{"count": 5}]
    mock_synth_llm.return_value = _llm("There are 5 customers.")

    graph = build_graph()
    result = graph.invoke({"question": "How many customers are there?"})

    assert result["db_targets"] == ["sales_db"]
    assert result["final_answer"] == "There are 5 customers."
    assert result["error"] is None


@patch("src.agent.nodes.synthesizer.get_llm")
@patch("src.agent.nodes.executor.execute_query")
@patch("src.agent.nodes.executor.get_inventory_engine")
@patch("src.agent.nodes.schema_injector.get_schema")
@patch("src.agent.nodes.schema_injector.get_inventory_engine")
@patch("src.agent.nodes.sql_generator.get_llm")
def test_full_pipeline_inventory_question(
    mock_gen_llm, mock_schema_inv, mock_get_schema,
    mock_exec_inv, mock_exec_query, mock_synth_llm,
):
    mock_gen_llm.return_value = _llm("SELECT product_id FROM stock_levels WHERE quantity_on_hand < 10")
    mock_get_schema.return_value = "Table: stock_levels\n  product_id INTEGER"
    mock_exec_query.return_value = [{"product_id": 101}]
    mock_synth_llm.return_value = _llm("Product 101 is low on stock.")

    graph = build_graph()
    result = graph.invoke({"question": "Which products are low on stock?"})

    assert result["db_targets"] == ["inventory_db"]
    assert result["final_answer"] == "Product 101 is low on stock."
