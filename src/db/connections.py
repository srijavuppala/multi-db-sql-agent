"""
SQLAlchemy connection factory for the multi-db-sql-agent.

Usage:
    from src.db.connections import get_sales_engine, verify_connection

    # Application code (read-only):
    engine = get_sales_engine(readonly=True)

    # Seed scripts only (admin):
    engine = get_sales_engine(readonly=False)

Environment variables (loaded from .env):
    SALES_DB_READONLY_URL  — postgresql+psycopg://app_readonly:...@localhost:5432/sales_db
    SALES_DB_ADMIN_URL     — postgresql+psycopg://postgres:...@localhost:5432/sales_db
"""
import os
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.engine import Engine

load_dotenv()

# Default fallback values match .env.example placeholders.
# In production, override via environment variables.
_DEFAULT_READONLY_URL = (
    "postgresql+psycopg://app_readonly:changeme_readonly@localhost:5432/sales_db"
)
_DEFAULT_ADMIN_URL = (
    "postgresql+psycopg://postgres:changeme@localhost:5432/sales_db"
)


def get_sales_engine(readonly: bool = True) -> Engine:
    """Return a SQLAlchemy Engine connected to sales_db.

    Args:
        readonly: If True, uses the app_readonly role (SELECT only).
                  If False, uses the postgres admin role (seed scripts only).

    Returns:
        SQLAlchemy Engine instance. Connection pool is managed automatically.

    Raises:
        Nothing on construction — connection errors surface on first use.
    """
    if readonly:
        url = os.getenv("SALES_DB_READONLY_URL", _DEFAULT_READONLY_URL)
    else:
        url = os.getenv("SALES_DB_ADMIN_URL", _DEFAULT_ADMIN_URL)

    return create_engine(
        url,
        pool_pre_ping=True,   # Detect and discard stale connections
        echo=False,
    )


def verify_connection(engine: Engine) -> bool:
    """Check if the engine can reach the database.

    Returns:
        True if a SELECT 1 succeeds, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Connection check failed: {e}")
        return False


def wait_for_db(engine: Engine, retries: int = 10, delay: float = 2.0) -> None:
    """Block until the database is reachable or raise RuntimeError.

    Used by seed scripts to wait for Docker container readiness.

    Args:
        engine: SQLAlchemy Engine to test.
        retries: Number of attempts before giving up.
        delay: Seconds between attempts.

    Raises:
        RuntimeError: If database is not available after all retries.
    """
    for i in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"Database ready after {i} retries.")
            return
        except OperationalError:
            print(f"Database not ready, retry {i + 1}/{retries} ...")
            time.sleep(delay)
    raise RuntimeError(
        f"Database not available after {retries} retries. "
        "Ensure `docker compose up --wait` has been run."
    )


# ── Inventory DB (SQLite) ─────────────────────────────────────────────────────

# Absolute path derived from this file's location to avoid CWD-relative ambiguity.
# connections.py lives at: multi-db-sql-agent/src/db/connections.py
# inventory.db lives at:   multi-db-sql-agent/db/inventory.db
_AGENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DEFAULT_INVENTORY_URL = f"sqlite:///{os.path.join(_AGENT_ROOT, 'db', 'inventory.db')}"


def get_inventory_engine() -> Engine:
    """Return a SQLAlchemy Engine connected to inventory_db (SQLite).

    No readonly/admin split — SQLite uses file-level access control.
    The DB file is created automatically by SQLite on first connection.

    Environment variables (loaded from .env):
        INVENTORY_DB_URL — sqlite:///./db/inventory.db
                           (defaults to absolute path relative to this file)
    """
    url = os.getenv("INVENTORY_DB_URL", _DEFAULT_INVENTORY_URL)
    return create_engine(
        url,
        pool_pre_ping=True,
        echo=False,
    )
