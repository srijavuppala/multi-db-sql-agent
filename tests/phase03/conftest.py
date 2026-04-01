"""
Shared fixtures for Phase 3 tests.

Uses SQLite in-memory databases so tests run without Docker or seed scripts.
"""
import sys
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Ensure project root is on sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


@pytest.fixture(scope="session")
def sqlite_engine() -> Engine:
    """In-memory SQLite engine seeded with a minimal sales-like schema."""
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE customers (
                id      INTEGER PRIMARY KEY,
                name    TEXT NOT NULL,
                email   TEXT NOT NULL,
                city    TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE orders (
                id          INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                total_amount REAL NOT NULL
            )
        """))
        conn.execute(text("""
            INSERT INTO customers (id, name, email, city)
            VALUES (1, 'Alice', 'alice@example.com', 'NYC'),
                   (2, 'Bob',   'bob@example.com',   'LA')
        """))
        conn.execute(text("""
            INSERT INTO orders (id, customer_id, total_amount)
            VALUES (1, 1, 99.99),
                   (2, 1, 49.50),
                   (3, 2, 200.00)
        """))
    return engine
