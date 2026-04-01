"""
Phase 3 — TOOL-01 tests.
Verifies: get_schema() extracts table/column info correctly.
"""
from src.tools.schema import get_schema, get_schema_for_prompt


def test_get_schema_contains_table_names(sqlite_engine):
    """TOOL-01: Schema string includes all table names."""
    schema = get_schema(sqlite_engine, db_name="test_db")
    assert "customers" in schema
    assert "orders" in schema


def test_get_schema_contains_column_names(sqlite_engine):
    """TOOL-01: Schema string includes column names for each table."""
    schema = get_schema(sqlite_engine, db_name="test_db")
    assert "name" in schema
    assert "email" in schema
    assert "total_amount" in schema


def test_get_schema_header_comment(sqlite_engine):
    """TOOL-01: Schema string includes the db_name header comment."""
    schema = get_schema(sqlite_engine, db_name="my_db")
    assert "-- my_db schema" in schema


def test_get_schema_no_header_when_no_db_name(sqlite_engine):
    """TOOL-01: Schema string has no header when db_name is empty."""
    schema = get_schema(sqlite_engine, db_name="")
    assert schema.startswith("Table:")


def test_get_schema_for_prompt_combines_schemas(sqlite_engine):
    """TOOL-01: get_schema_for_prompt() merges schemas from multiple engines."""
    combined = get_schema_for_prompt({
        "sales_db": sqlite_engine,
        "inventory_db": sqlite_engine,
    })
    assert "-- sales_db schema" in combined
    assert "-- inventory_db schema" in combined
