"""
LangGraph agent state.

A single TypedDict flows through every node in the graph. Nodes return
partial dicts — LangGraph merges them into the running state automatically.

Fields
------
question      : The original user question (never mutated after input).
db_targets    : Which DB(s) the router chose: "sales_db", "inventory_db", "both".
schema        : Schema string injected by the Schema Injector node.
sql           : SQL string produced (or rewritten) by the SQL Generator node.
result        : Rows returned by the SQL Executor node (list of plain dicts).
error         : Last execution error message, or None if the last run succeeded.
retry_count   : Number of self-correction retries attempted so far (max 3).
final_answer  : Human-readable answer assembled by the Synthesizer node.
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
    schema: str             # Formatted schema string for the target DB(s)

    # ── SQL generation / correction ────────────────────────────────────────
    sql: str                # Generated (or corrected) SQL statement
    error: str | None       # Execution error from the last attempt, or None
    retry_count: int        # Incremented by self-correction loop (cap: 3)

    # ── Execution ──────────────────────────────────────────────────────────
    result: list[dict[str, Any]]  # Rows returned by execute_query()

    # ── Synthesis ──────────────────────────────────────────────────────────
    final_answer: str       # Human-readable answer to return to the user
