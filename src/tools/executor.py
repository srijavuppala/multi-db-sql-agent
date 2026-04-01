"""
Safe SQL execution tool.

Validates SQL against a sqlglot AST before running it — mutation statements
(INSERT, UPDATE, DELETE, DROP, CREATE, ALTER) are rejected before they reach
the database.  This is a defence-in-depth measure; Postgres also enforces this
via the app_readonly role.

Usage:
    from src.tools.executor import execute_query, validate_readonly_sql
    from src.db.connections import get_sales_engine

    rows = execute_query(get_sales_engine(), "SELECT id, name FROM customers LIMIT 5")
    # -> [{"id": 1, "name": "Alice"}, ...]

    # Raises ValueError for mutations even before hitting the DB:
    execute_query(engine, "DELETE FROM customers")  # ValueError
"""
from __future__ import annotations

from typing import Any

import sqlglot
import sqlglot.expressions as exp
from sqlalchemy import text
from sqlalchemy.engine import Engine

# Statement types that are forbidden in agent-generated SQL.
_FORBIDDEN_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.Command,  # catches raw DDL that sqlglot parses as Command
)


def validate_readonly_sql(sql: str) -> None:
    """Parse *sql* with sqlglot and raise ValueError if it contains mutations.

    Args:
        sql: Raw SQL string to validate.

    Raises:
        ValueError: If the SQL contains a forbidden statement type, or if
                    sqlglot cannot parse it at all.
    """
    try:
        statements = sqlglot.parse(sql.strip())
    except sqlglot.errors.ParseError as exc:
        raise ValueError(f"SQL parse error: {exc}") from exc

    non_null = [s for s in statements if s is not None]
    if not non_null:
        raise ValueError("Empty SQL statement.")

    for stmt in non_null:
        if isinstance(stmt, _FORBIDDEN_TYPES):
            raise ValueError(
                f"Mutation SQL is not allowed: {type(stmt).__name__}. "
                "Only SELECT statements are permitted."
            )


def execute_query(engine: Engine, sql: str) -> list[dict[str, Any]]:
    """Validate and execute a read-only SQL query.

    Runs AST-level validation first (sqlglot), then executes via SQLAlchemy.
    Results are returned as a list of plain dicts for easy serialisation.

    Args:
        engine: SQLAlchemy engine for the target database.
        sql:    SELECT statement to execute.

    Returns:
        List of row dicts, e.g. [{"id": 1, "name": "Alice"}, ...].
        Empty list if the query returns no rows.

    Raises:
        ValueError:  If *sql* contains mutation statements.
        sqlalchemy.exc.SQLAlchemyError: If the query fails at the DB level.
    """
    validate_readonly_sql(sql)

    with engine.connect() as conn:
        result = conn.execute(text(sql))
        return [dict(row._mapping) for row in result]
