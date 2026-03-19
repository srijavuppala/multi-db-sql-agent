"""
Phase 1 — DATA-01 tests.
Verifies: Postgres container reachable, sales_db accessible, required tables exist.
Requires: docker compose up --wait (skips gracefully if not running)
"""
from sqlalchemy import text, inspect


def test_postgres_reachable(admin_engine):
    """DATABASE-01: Can connect to sales_db as admin user."""
    with admin_engine.connect() as conn:
        result = conn.execute(text("SELECT current_database()"))
        db_name = result.scalar()
    assert db_name == "sales_db", f"Expected 'sales_db', got '{db_name}'"


def test_tables_exist(admin_engine):
    """DATA-01: customers, orders, order_items tables exist in public schema."""
    inspector = inspect(admin_engine)
    existing_tables = set(inspector.get_table_names(schema="public"))
    required_tables = {"customers", "orders", "order_items"}
    missing = required_tables - existing_tables
    assert not missing, f"Missing tables in sales_db: {missing}"
