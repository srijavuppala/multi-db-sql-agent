"""
SQL Executor Node (Phase 5).

A LangGraph-compatible node that:
  1. Picks the right SQLAlchemy engine based on state["db_targets"].
  2. Calls execute_query() (which validates + runs the SQL).
  3. On success  → returns {"result": rows, "error": None}
  4. On failure  → returns {"error": message, "retry_count": retry_count + 1}
     leaving `result` untouched so the self-correction loop can inspect it.

The node does NOT decide whether to retry — that logic lives in the
conditional edge `should_retry()` in graph.py.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from src.agent.state import AgentState
from src.db.connections import get_inventory_engine, get_sales_engine
from src.tools.executor import execute_query

_MAX_RETRIES = 3


def _engine_for_target(db_name: str) -> Engine:
    """Return the read-only engine for a named database.

    Args:
        db_name: "sales_db" or "inventory_db"

    Raises:
        ValueError: If db_name is not recognised.
    """
    if db_name == "sales_db":
        return get_sales_engine(readonly=True)
    if db_name == "inventory_db":
        return get_inventory_engine()
    raise ValueError(f"Unknown db target: {db_name!r}")


def executor_node(state: AgentState) -> AgentState:
    """LangGraph node — execute the generated SQL against the target database.

    Reads from state:
        sql         — SQL statement produced by sql_generation_node
        db_targets  — list of DB names; uses the first entry for single-DB queries
        retry_count — current retry depth (incremented on failure)

    Writes to state (success):
        result      — list of row dicts
        error       — None

    Writes to state (failure):
        error       — exception message string
        retry_count — incremented by 1

    Returns:
        Partial AgentState dict.
    """
    sql = state.get("sql", "")
    db_targets = state.get("db_targets") or ["sales_db"]
    retry_count = state.get("retry_count") or 0

    # Phase 5: single-DB execution (cross-DB merge comes in Phase 6)
    target = db_targets[0]

    try:
        engine = _engine_for_target(target)
        rows = execute_query(engine, sql)
        return {"result": rows, "error": None}
    except Exception as exc:
        return {
            "error": str(exc),
            "retry_count": retry_count + 1,
        }


# ── Conditional edge ──────────────────────────────────────────────────────────

def should_retry(state: AgentState) -> str:
    """LangGraph conditional edge function.

    Returns:
        "retry" — if there is an error and retries remain
        "done"  — if the query succeeded or retry limit is reached
    """
    if state.get("error") and (state.get("retry_count") or 0) < _MAX_RETRIES:
        return "retry"
    return "done"
