"""Phase 6 — AGENT-06: router_node keyword classification tests."""
from src.agent.nodes.router import router_node


def test_routes_customer_question_to_sales():
    result = router_node({"question": "How many customers are in NYC?"})
    assert result["db_targets"] == ["sales_db"]


def test_routes_order_question_to_sales():
    result = router_node({"question": "Show me total revenue by order"})
    assert result["db_targets"] == ["sales_db"]


def test_routes_stock_question_to_inventory():
    result = router_node({"question": "Which products are low on stock?"})
    assert result["db_targets"] == ["inventory_db"]


def test_routes_supplier_question_to_inventory():
    result = router_node({"question": "List all suppliers by country"})
    assert result["db_targets"] == ["inventory_db"]


def test_routes_cross_db_question_to_both():
    result = router_node({
        "question": "Which customers ordered products that are low on stock?"
    })
    assert set(result["db_targets"]) == {"sales_db", "inventory_db"}


def test_defaults_to_sales_for_unrecognised_question():
    result = router_node({"question": "What is the meaning of life?"})
    assert result["db_targets"] == ["sales_db"]


def test_returns_only_db_targets_key():
    result = router_node({"question": "Show revenue"})
    assert set(result.keys()) == {"db_targets"}
