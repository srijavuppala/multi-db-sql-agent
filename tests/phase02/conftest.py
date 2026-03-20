"""
Shared pytest fixtures for Phase 2 integration tests.

Requires inventory.db to exist (run seed_inventory_db.py first).
Skips gracefully if the DB file is absent or get_inventory_engine is not yet added.
"""
import sys
import os
import pytest

# Allow imports from multi-db-sql-agent/src/ and db/seeds/
_project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_agent_root = os.path.join(_project_root, "multi-db-sql-agent")
_seeds_root = os.path.join(_agent_root, "db", "seeds")

for _path in [_project_root, _agent_root, _seeds_root]:
    if _path not in sys.path:
        sys.path.insert(0, _path)


def _try_import_inventory_engine():
    """Return get_inventory_engine or None if not yet added to connections.py."""
    try:
        from src.db.connections import get_inventory_engine
        return get_inventory_engine
    except ImportError:
        return None


@pytest.fixture(scope="session")
def inventory_engine():
    """SQLAlchemy engine for inventory_db (SQLite).

    Skips if:
    - get_inventory_engine not yet added to src/db/connections.py (Plan 02 pending)
    - inventory.db file does not exist (seed_inventory_db.py not run yet)
    """
    from sqlalchemy import text

    get_inventory_engine = _try_import_inventory_engine()
    if get_inventory_engine is None:
        pytest.skip("get_inventory_engine not yet added to src/db/connections.py (Plan 02 pending)")

    engine = get_inventory_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("inventory.db not found or not queryable — run seed_inventory_db.py first")
    return engine
