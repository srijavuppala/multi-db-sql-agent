"""
Prompt templates for the SQL agent.

All templates are plain Python f-string factories so they stay readable and
easy to iterate on without a heavy template library.

Templates
---------
build_sql_generation_prompt  — first-attempt SQL generation
build_sql_correction_prompt  — self-correction after an execution error
"""
from __future__ import annotations

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
