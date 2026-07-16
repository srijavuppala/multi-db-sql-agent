"""
Phase 3 — TOOL-02 tests.
Verifies: execute_query() runs SELECT correctly and rejects mutations.
"""
import pytest
from src.tools.executor import execute_query, validate_readonly_sql


# ── validate_readonly_sql ─────────────────────────────────────────────────────

def test_select_passes_validation():
    """TOOL-02: A plain SELECT does not raise."""
    validate_readonly_sql("SELECT id, name FROM customers WHERE id = 1")


def test_insert_rejected():
    """TOOL-02: INSERT raises ValueError."""
    with pytest.raises(ValueError, match="Mutation SQL"):
        validate_readonly_sql("INSERT INTO customers (name) VALUES ('Eve')")


def test_update_rejected():
    """TOOL-02: UPDATE raises ValueError."""
    with pytest.raises(ValueError, match="Mutation SQL"):
        validate_readonly_sql("UPDATE customers SET name = 'Eve' WHERE id = 1")


def test_delete_rejected():
    """TOOL-02: DELETE raises ValueError."""
    with pytest.raises(ValueError, match="Mutation SQL"):
        validate_readonly_sql("DELETE FROM customers WHERE id = 1")


def test_drop_rejected():
    """TOOL-02: DROP TABLE raises ValueError."""
    with pytest.raises(ValueError, match="Mutation SQL"):
        validate_readonly_sql("DROP TABLE customers")


def test_empty_sql_rejected():
    """TOOL-02: Empty string raises ValueError."""
    with pytest.raises(ValueError):
        validate_readonly_sql("   ")


# ── execute_query ─────────────────────────────────────────────────────────────

def test_execute_select_returns_rows(sqlite_engine):
    """TOOL-02: execute_query returns list of dicts for a valid SELECT."""
    rows = execute_query(sqlite_engine, "SELECT id, name FROM customers ORDER BY id")
    assert len(rows) == 2
    assert rows[0]["name"] == "Alice"
    assert rows[1]["name"] == "Bob"


def test_execute_returns_empty_list_for_no_rows(sqlite_engine):
    """TOOL-02: execute_query returns [] when query matches no rows."""
    rows = execute_query(sqlite_engine, "SELECT * FROM customers WHERE id = 999")
    assert rows == []


def test_execute_result_is_plain_dicts(sqlite_engine):
    """TOOL-02: execute_query returns plain dicts, not SQLAlchemy Row objects."""
    rows = execute_query(sqlite_engine, "SELECT id, name FROM customers LIMIT 1")
    assert isinstance(rows[0], dict)


def test_execute_rejects_mutation_before_db(sqlite_engine):
    """TOOL-02: execute_query raises ValueError before touching the DB."""
    with pytest.raises(ValueError, match="Mutation SQL"):
        execute_query(sqlite_engine, "DELETE FROM customers")


def test_execute_select_with_aggregation(sqlite_engine):
    """TOOL-02: Aggregation queries work correctly."""
    rows = execute_query(
        sqlite_engine,
        "SELECT customer_id, SUM(total_amount) as total FROM orders GROUP BY customer_id ORDER BY customer_id",
    )
    assert len(rows) == 2
    assert abs(rows[0]["total"] - 149.49) < 0.01  # Alice: 99.99 + 49.50
