"""
SQL Generation Node (Phase 4).

A LangGraph-compatible node that:
  1. Builds a prompt from the current AgentState (question + schema).
  2. Calls the LLM to generate a SQL SELECT statement.
  3. Strips any markdown fences the LLM may have added.
  4. Returns a state patch with the generated SQL (and resets error/retry_count
     on the first attempt).

For self-correction (Phase 5) the same node can be invoked again — it detects
a non-None `error` in state and switches to the correction prompt automatically.

Usage (standalone):
    from src.agent.nodes.sql_generator import sql_generation_node
    from src.agent.state import AgentState

    state: AgentState = {
        "question": "How many customers are in NYC?",
        "schema": "...",
        "db_targets": ["sales_db"],
    }
    new_state = sql_generation_node(state)
    print(new_state["sql"])
"""
from __future__ import annotations

import re

from src.agent.prompts import (
    build_sql_correction_prompt,
    build_sql_generation_prompt,
)
from src.agent.state import AgentState
from src.llm.client import get_llm

# Regex to strip ```sql ... ``` or plain ``` ... ``` fences
_FENCE_RE = re.compile(r"```(?:sql)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def _extract_sql(raw: str) -> str:
    """Strip markdown code fences from LLM output and return clean SQL.

    If no fence is found the raw text is returned stripped, so the node
    degrades gracefully when the model follows instructions correctly.
    """
    match = _FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()
    return raw.strip()


def sql_generation_node(state: AgentState) -> AgentState:
    """LangGraph node — generate (or correct) a SQL statement.

    Reads from state:
        question    — user's natural-language question
        schema      — schema string injected by the Schema Injector
        db_targets  — list of DB names the query should target
        error       — if set, switches to the correction prompt
        sql         — previous (failed) SQL, used in correction prompt
        retry_count — tracked externally; this node does not increment it

    Writes to state:
        sql         — newly generated SQL string

    Returns:
        Partial AgentState dict with `sql` updated.
    """
    llm = get_llm()

    question = state.get("question", "")
    schema = state.get("schema", "")
    db_targets = state.get("db_targets", [])
    error = state.get("error")

    if error:
        # Self-correction path (Phase 5 calls this node again after an error)
        messages = build_sql_correction_prompt(
            question=question,
            schema=schema,
            sql=state.get("sql", ""),
            error=error,
        )
    else:
        messages = build_sql_generation_prompt(
            question=question,
            schema=schema,
            db_targets=db_targets,
        )

    response = llm.invoke(messages)
    sql = _extract_sql(str(response.content))

    return {"sql": sql}
