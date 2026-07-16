"""Phase 6 — AGENT-07: schema_injector_node tests (DB calls mocked)."""
from unittest.mock import MagicMock, patch

from src.agent.nodes.schema_injector import schema_injector_node


def _mock_engine():
    engine = MagicMock()
    return engine


@patch("src.agent.nodes.schema_injector.get_schema")
@patch("src.agent.nodes.schema_injector.get_sales_engine")
def test_injects_sales_schema(mock_sales_engine, mock_get_schema):
    mock_get_schema.return_value = "-- sales_db schema\nTable: customers\n  id INTEGER"

    result = schema_injector_node({"db_targets": ["sales_db"]})

    assert "schemas_by_db" in result
    assert "schema" in result
    assert "sales_db" in result["schemas_by_db"]


@patch("src.agent.nodes.schema_injector.get_schema")
@patch("src.agent.nodes.schema_injector.get_inventory_engine")
def test_injects_inventory_schema(mock_inv_engine, mock_get_schema):
    mock_get_schema.return_value = "-- inventory_db schema\nTable: products\n  product_id INTEGER"

    result = schema_injector_node({"db_targets": ["inventory_db"]})

    assert "inventory_db" in result["schemas_by_db"]


@patch("src.agent.nodes.schema_injector.get_schema")
@patch("src.agent.nodes.schema_injector.get_inventory_engine")
@patch("src.agent.nodes.schema_injector.get_sales_engine")
def test_injects_both_schemas_for_multi_db(mock_sales, mock_inv, mock_get_schema):
    mock_get_schema.side_effect = lambda engine, db_name: f"-- {db_name} schema"

    result = schema_injector_node({"db_targets": ["sales_db", "inventory_db"]})

    assert "sales_db" in result["schemas_by_db"]
    assert "inventory_db" in result["schemas_by_db"]
    assert "sales_db" in result["schema"]
    assert "inventory_db" in result["schema"]


@patch("src.agent.nodes.schema_injector.get_schema")
@patch("src.agent.nodes.schema_injector.get_sales_engine")
def test_defaults_to_sales_when_no_targets(mock_sales, mock_get_schema):
    mock_get_schema.return_value = "-- sales_db schema"

    result = schema_injector_node({})  # no db_targets

    assert "sales_db" in result["schemas_by_db"]
