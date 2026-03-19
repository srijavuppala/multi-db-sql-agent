"""
Shared pytest fixtures for Phase 1 integration tests.

All fixtures that require a running Postgres container will skip the test
gracefully (pytest.skip) if the container is not available. This prevents
CI failures when Docker is not running locally.
"""
import sys
import os
import pytest

# Allow imports from multi-db-sql-agent/src/
# This path manipulation is required because the project root layout puts
# source code in multi-db-sql-agent/src/ which is not a top-level package.
_project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_agent_root = os.path.join(_project_root, "multi-db-sql-agent")
_seeds_root = os.path.join(_agent_root, "db", "seeds")

for _path in [_project_root, _agent_root, _seeds_root]:
    if _path not in sys.path:
        sys.path.insert(0, _path)


def _try_import_engine():
    """Return get_sales_engine or None if src/ not yet created."""
    try:
        from src.db.connections import get_sales_engine
        return get_sales_engine
    except ImportError:
        return None


@pytest.fixture(scope="session")
def admin_engine():
    """SQLAlchemy engine using the postgres admin role.

    Skips the test if:
    - src/db/connections.py does not exist yet (Plan 03 not run)
    - Postgres container is not reachable
    """
    get_sales_engine = _try_import_engine()
    if get_sales_engine is None:
        pytest.skip("src/db/connections.py not yet created (Plan 03 pending)")

    from sqlalchemy.exc import OperationalError
    engine = get_sales_engine(readonly=False)
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        pytest.skip("Postgres container not running — run `docker compose up --wait` first")
    return engine


@pytest.fixture(scope="session")
def readonly_engine():
    """SQLAlchemy engine using the app_readonly role.

    Skips the test if:
    - src/db/connections.py does not exist yet (Plan 03 not run)
    - Postgres container is not reachable
    """
    get_sales_engine = _try_import_engine()
    if get_sales_engine is None:
        pytest.skip("src/db/connections.py not yet created (Plan 03 pending)")

    from sqlalchemy.exc import OperationalError
    engine = get_sales_engine(readonly=True)
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        pytest.skip("Postgres container not running or app_readonly role not yet created")
    return engine
