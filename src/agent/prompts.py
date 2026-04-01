"""
Prompt templates for the SQL agent.

All templates are plain Python f-string factories so they stay readable and
easy to iterate on without a heavy template library.

Templates
---------
build_sql_generation_prompt  — first-attempt SQL generation
build_sql_correction_prompt  — self-correction after an execution error
build_synthesis_prompt       — natural-language answer from query results
"""
from __future__ import annotations
import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

_SQL_SYSTEM = """\
You are an expert SQL assistant. Your job is to write a single, correct SQL \
SELECT statement that answers the user's question using only the database \
schema provided.

Rules:
- Output ONLY the SQL statement — no explanation, no markdown, no code fences.
- Use only SELECT statements. Never write INSERT, UPDATE, DELETE, DROP, or CREATE.
- Use table and column names exactly as they appear in the schema.
- If the question cannot be answered with the given schema, reply with exactly:
  CANNOT_ANSWER
"""


def build_sql_generation_prompt(
    question: str,
    schema: str,
    db_targets: list[str],
) -> list[SystemMessage | HumanMessage]:
    """Return a LangChain message list for first-attempt SQL generation.

    Args:
        question:   Natural-language question from the user.
        schema:     Formatted schema string from get_schema() / get_schema_for_prompt().
        db_targets: List of DB names the query targets (for context in the prompt).

    Returns:
        [SystemMessage, HumanMessage] ready to pass to llm.invoke().
    """
    db_label = " and ".join(db_targets) if db_targets else "the database"
    human_text = (
        f"Database schema for {db_label}:\n\n"
        f"{schema}\n\n"
        f"Question: {question}"
    )
    return [
        SystemMessage(content=_SQL_SYSTEM),
        HumanMessage(content=human_text),
    ]


def build_sql_correction_prompt(
    question: str,
    schema: str,
    sql: str,
    error: str,
) -> list[SystemMessage | HumanMessage]:
    """Return a LangChain message list for self-correction after an error.

    Args:
        question: Original user question.
        schema:   Formatted schema string.
        sql:      The SQL that failed.
        error:    The error message returned by the executor.

    Returns:
        [SystemMessage, HumanMessage] ready to pass to llm.invoke().
    """
    human_text = (
        f"Database schema:\n\n{schema}\n\n"
        f"Question: {question}\n\n"
        f"The following SQL produced an error:\n```sql\n{sql}\n```\n\n"
        f"Error:\n{error}\n\n"
        "Please write a corrected SQL SELECT statement that fixes the error."
    )
    return [
        SystemMessage(content=_SQL_SYSTEM),
        HumanMessage(content=human_text),
    ]


_SYNTHESIS_SYSTEM = (
    "You are a helpful data analyst. "
    "Given a user question and database query results, write a clear and concise answer. "
    "Be specific — include numbers, names, and values from the data. "
    "Do not show SQL or raw JSON in your answer."
)


def build_synthesis_prompt(
    question: str,
    results: dict,
    sql: str,
) -> list:
    """Return a LangChain message list for the synthesis node.

    Args:
        question: Original user question.
        results:  Dict of db_name -> list of row dicts (single-DB uses key "result").
        sql:      The SQL that was executed (for context).

    Returns:
        [SystemMessage, HumanMessage] ready to pass to llm.invoke().
    """
    results_text = json.dumps(results, indent=2, default=str)
    if len(results_text) > 4000:
        results_text = results_text[:4000] + "\n... (truncated)"

    human_text = (
        f"Question: {question}\n\n"
        f"SQL executed:\n{sql}\n\n"
        f"Query results:\n{results_text}\n\n"
        "Please answer the question based on these results."
    )
    return [
        SystemMessage(content=_SYNTHESIS_SYSTEM),
        HumanMessage(content=human_text),
    ]
