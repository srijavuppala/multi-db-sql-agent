"""
LangGraph agent state.

A single TypedDict flows through every node in the graph. Nodes return
partial dicts — LangGraph merges them into the running state automatically.

Fields
------
question        : The original user question (never mutated after input).
db_targets      : Which DB(s) the router chose: ["sales_db"], ["inventory_db"], or both.
schema          : Combined schema string injected by the Schema Injector node.
schemas_by_db   : Per-DB schema strings used by the multi-DB SQL generator.
sql             : SQL string for single-DB queries.
sql_by_db       : Per-DB SQL strings for cross-DB queries.
error           : Last execution error message, or None if the last run succeeded.
retry_count     : Number of self-correction retries attempted so far (max 3).
result          : Rows from a single-DB execution.
results_by_db   : Rows per DB for cross-DB executions.
final_answer    : Human-readable answer assembled by the Synthesizer node.
"""
from __future__ import annotations

from typing import Any
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """Shared state that flows through the LangGraph agent pipeline."""

    # ── Input ──────────────────────────────────────────────────────────────
    question: str           # Original natural-language question

    # ── Router output ──────────────────────────────────────────────────────
    db_targets: list[str]   # e.g. ["sales_db"] or ["sales_db", "inventory_db"]

    # ── Schema injection ───────────────────────────────────────────────────
    schema: str                     # Combined schema for all targeted DBs
    schemas_by_db: dict[str, str]   # db_name → individual schema string

    # ── SQL generation / correction ────────────────────────────────────────
    sql: str                    # Single-DB SQL statement
    sql_by_db: dict[str, str]   # Multi-DB: db_name → SQL string
    error: str | None           # Execution error from the last attempt, or None
    retry_count: int            # Incremented by self-correction loop (cap: 3)

    # ── Execution ──────────────────────────────────────────────────────────
    result: list[dict[str, Any]]                    # Single-DB rows
    results_by_db: dict[str, list[dict[str, Any]]]  # Multi-DB rows per DB

    # ── Synthesis ──────────────────────────────────────────────────────────
    final_answer: str       # Human-readable answer to return to the user
