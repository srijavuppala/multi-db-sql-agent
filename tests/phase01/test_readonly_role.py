"""
Phase 1 — SEC-02 tests.
Verifies: app_readonly role can SELECT; INSERT/UPDATE/DROP are rejected.
Requires: docker compose up --wait (skips gracefully if not running)
"""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError


def test_select_succeeds(readonly_engine):
    """SEC-02: app_readonly role can SELECT from all three tables."""
    with readonly_engine.connect() as conn:
        for table in ("customers", "orders", "order_items"):
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            assert count is not None, f"SELECT from {table} returned None"


def test_mutations_rejected(readonly_engine):
    """SEC-02: app_readonly role is rejected on INSERT, UPDATE, DROP."""
    mutations = [
        ("INSERT", "INSERT INTO customers (name, email, city) VALUES ('test', 'test@test.com', 'NYC')"),
        ("UPDATE", "UPDATE customers SET city = 'LA' WHERE id = 1"),
        ("DROP",   "DROP TABLE customers"),
    ]
    for op_name, sql in mutations:
        with readonly_engine.connect() as conn:
            with pytest.raises(ProgrammingError, match="permission denied"):
                conn.execute(text(sql))
                conn.commit()


def test_sqlalchemy_readonly_engine(readonly_engine):
    """SEC-02: SQLAlchemy create_engine() with read-only URL connects without error."""
    with readonly_engine.connect() as conn:
        result = conn.execute(text("SELECT current_user"))
        user = result.scalar()
    assert user == "app_readonly", (
        f"Expected current_user='app_readonly', got '{user}'. "
        "Check SALES_DB_READONLY_URL in .env points to the app_readonly role."
    )
