"""
Phase 1 — DATA-02 tests.
Verifies: >= 100 rows in order_items (proxy for seeding complete), data quality checks.
Requires: docker compose up --wait AND seed script run (skips gracefully if not)
"""
import pytest
from sqlalchemy import text


MIN_ROWS = 100


def _row_count(conn, table: str) -> int:
    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
    return result.scalar()


def test_minimum_row_counts(admin_engine):
    """DATA-02: order_items has at least 100 rows (seed complete)."""
    with admin_engine.connect() as conn:
        counts = {
            "customers": _row_count(conn, "customers"),
            "orders": _row_count(conn, "orders"),
            "order_items": _row_count(conn, "order_items"),
        }
    # order_items is the densest table; use it as proxy
    assert counts["order_items"] >= MIN_ROWS, (
        f"Expected >= {MIN_ROWS} order_items rows, got {counts['order_items']}. "
        f"Run: uv run python multi-db-sql-agent/db/seeds/seed_sales_db.py"
    )
    # Sanity: customers and orders must also be non-empty
    assert counts["customers"] > 0, "customers table is empty — seed not run"
    assert counts["orders"] > 0, "orders table is empty — seed not run"


def test_seed_data_quality(admin_engine):
    """DATA-02: Seed data has realistic values (non-null names, valid emails, positive amounts)."""
    with admin_engine.connect() as conn:
        # Check no null names or emails in customers
        null_check = conn.execute(text(
            "SELECT COUNT(*) FROM customers WHERE name IS NULL OR email IS NULL"
        )).scalar()
        assert null_check == 0, f"{null_check} customers have NULL name or email"

        # Check email contains '@'
        bad_email = conn.execute(text(
            "SELECT COUNT(*) FROM customers WHERE email NOT LIKE '%@%'"
        )).scalar()
        assert bad_email == 0, f"{bad_email} customers have invalid email format"

        # Check total_amount > 0 in orders
        bad_amount = conn.execute(text(
            "SELECT COUNT(*) FROM orders WHERE total_amount <= 0"
        )).scalar()
        assert bad_amount == 0, f"{bad_amount} orders have non-positive total_amount"

        # Check quantity > 0 in order_items
        bad_qty = conn.execute(text(
            "SELECT COUNT(*) FROM order_items WHERE quantity <= 0"
        )).scalar()
        assert bad_qty == 0, f"{bad_qty} order_items have non-positive quantity"
