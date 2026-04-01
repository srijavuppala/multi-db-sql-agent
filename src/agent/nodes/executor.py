"""
SQL Executor Node (Phase 5 / updated Phase 6).

Single-DB:  executes state["sql"] against the first db_target.
Multi-DB:   iterates state["sql_by_db"], executes each against its DB,
            stores all results in state["results_by_db"].

On any failure the node records the error and increments retry_count so
the self-correction loop in graph.py can route back to sql_generation_node.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from src.agent.state import AgentState
from src.db.connections import get_inventory_engine, get_sales_engine
from src.tools.executor import execute_query

_MAX_RETRIES = 3


def _engine_for_target(db_name: str) -> Engine:
    if db_name == "sales_db":
        return get_sales_engine(readonly=True)
    if db_name == "inventory_db":
        return get_inventory_engine()
    raise ValueError(f"Unknown db target: {db_name!r}")


def executor_node(state: AgentState) -> AgentState:
    """LangGraph node — execute SQL against the target database(s).

    Single-DB path:
        Reads  state["sql"] and state["db_targets"][0].
        Writes state["result"] and state["error"].

    Multi-DB path:
        Reads  state["sql_by_db"].
        Writes state["results_by_db"] and state["error"].

    On failure, increments state["retry_count"] and sets state["error"].
    """
    retry_count = state.get("retry_count") or 0
    sql_by_db = state.get("sql_by_db")

    if sql_by_db:
        # ── Multi-DB execution ────────────────────────────────────────────
        results_by_db: dict = {}
        for db_name, sql in sql_by_db.items():
            try:
                engine = _engine_for_target(db_name)
                results_by_db[db_name] = execute_query(engine, sql)
            except Exception as exc:
                return {
                    "error": f"[{db_name}] {exc}",
                    "retry_count": retry_count + 1,
                }
        return {"results_by_db": results_by_db, "error": None}

    # ── Single-DB execution ───────────────────────────────────────────────
    sql = state.get("sql", "")
    db_targets = state.get("db_targets") or ["sales_db"]
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
    """Return 'retry' if there is an error and retries remain, else 'done'."""
    if state.get("error") and (state.get("retry_count") or 0) < _MAX_RETRIES:
        return "retry"
    return "done"
