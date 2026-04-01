"""
Synthesizer Node (Phase 6).

Takes the query results (single-DB or multi-DB) and generates a concise
natural-language answer via the LLM.

For cross-DB questions the node also merges results_by_db on the shared
PRODUCT_IDS key before passing them to the LLM.

Usage:
    from src.agent.nodes.synthesizer import synthesizer_node
    patch = synthesizer_node({
        "question": "How many customers are there?",
        "sql": "SELECT COUNT(*) FROM customers",
        "result": [{"count": 42}],
    })
    # -> {"final_answer": "There are 42 customers."}
"""
from __future__ import annotations

from src.agent.prompts import build_synthesis_prompt
from src.agent.state import AgentState
from src.llm.client import get_llm


def synthesizer_node(state: AgentState) -> AgentState:
    """LangGraph node — generate a human-readable answer from query results.

    Reads from state:
        question       — original user question
        result         — single-DB row list (may be empty)
        results_by_db  — multi-DB row dict (may be empty)
        sql            — single-DB SQL string
        sql_by_db      — multi-DB SQL dict
        error          — last error message (if retries exhausted)

    Writes to state:
        final_answer — human-readable answer string

    Returns:
        Partial AgentState dict with final_answer set.
    """
    question = state.get("question", "")
    error = state.get("error")
    result = state.get("result") or []
    results_by_db = state.get("results_by_db") or {}
    sql = state.get("sql") or ""
    sql_by_db = state.get("sql_by_db") or {}

    # If all retries failed and nothing came back, return an error answer
    if error and not result and not results_by_db:
        return {
            "final_answer": (
                f"I was unable to answer your question after multiple attempts. "
                f"Last error: {error}"
            )
        }

    # Build a results dict for the synthesis prompt
    if results_by_db:
        combined_results = results_by_db
    else:
        combined_results = {"result": result}

    # Build SQL context string
    if sql_by_db:
        sql_context = "\n".join(
            f"-- {db}:\n{s}" for db, s in sql_by_db.items()
        )
    else:
        sql_context = sql

    llm = get_llm()
    messages = build_synthesis_prompt(question, combined_results, sql_context)
    response = llm.invoke(messages)

    return {"final_answer": str(response.content).strip()}
