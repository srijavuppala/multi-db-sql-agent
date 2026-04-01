"""
SQL Generation Node (Phase 4 / updated Phase 6).

Single-DB:  generates one SQL statement stored in state["sql"].
Multi-DB:   generates one SQL per targeted DB, stored in state["sql_by_db"].

Self-correction: when state["error"] is set the node switches to the
correction prompt (Phase 5 behaviour) for whichever mode is active.
"""
from __future__ import annotations

import re

from src.agent.prompts import (
    build_sql_correction_prompt,
    build_sql_generation_prompt,
)
from src.agent.state import AgentState
from src.llm.client import get_llm

_FENCE_RE = re.compile(r"```(?:sql)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def _extract_sql(raw: str) -> str:
    """Strip markdown code fences; return plain SQL."""
    match = _FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()
    return raw.strip()


def _generate_for_db(
    llm,
    question: str,
    schema: str,
    db_name: str,
    error: str | None,
    prev_sql: str,
) -> str:
    """Call the LLM once for a single target DB."""
    if error:
        messages = build_sql_correction_prompt(
            question=question,
            schema=schema,
            sql=prev_sql,
            error=error,
        )
    else:
        messages = build_sql_generation_prompt(
            question=question,
            schema=schema,
            db_targets=[db_name],
        )
    response = llm.invoke(messages)
    return _extract_sql(str(response.content))


def sql_generation_node(state: AgentState) -> AgentState:
    """LangGraph node — generate (or correct) SQL for one or more target DBs.

    Single-DB  → returns {"sql": "..."}
    Multi-DB   → returns {"sql_by_db": {"sales_db": "...", "inventory_db": "..."}}
    """
    llm = get_llm()
    question = state.get("question", "")
    db_targets = state.get("db_targets") or ["sales_db"]
    error = state.get("error")
    schemas_by_db = state.get("schemas_by_db") or {}
    schema = state.get("schema", "")

    if len(db_targets) > 1:
        # Multi-DB: one LLM call per database
        prev_sql_by_db = state.get("sql_by_db") or {}
        sql_by_db: dict[str, str] = {}
        for db in db_targets:
            db_schema = schemas_by_db.get(db, schema)
            prev_sql = prev_sql_by_db.get(db, "")
            sql_by_db[db] = _generate_for_db(
                llm, question, db_schema, db, error, prev_sql
            )
        return {"sql_by_db": sql_by_db, "sql": ""}

    # Single-DB
    target = db_targets[0]
    db_schema = schemas_by_db.get(target, schema)
    sql = _generate_for_db(
        llm, question, db_schema, target, error, state.get("sql", "")
    )
    return {"sql": sql}
