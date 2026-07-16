"""
Schema extraction tool.

Introspects a SQLAlchemy engine and returns a human-readable schema string
suitable for injecting into an LLM prompt as context.

Usage:
    from src.tools.schema import get_schema
    from src.db.connections import get_sales_engine, get_inventory_engine

    sales_schema = get_schema(get_sales_engine(), db_name="sales_db")
    inv_schema   = get_schema(get_inventory_engine(), db_name="inventory_db")
"""
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.engine import Engine


def get_schema(engine: Engine, db_name: str = "") -> str:
    """Return a CREATE TABLE-style schema string for all tables in the DB.

    The output is deliberately concise — column names and types only — to
    minimise token usage when injecting into an LLM prompt.

    Example output:
        -- sales_db schema
        Table: customers
          id            INTEGER
          name          VARCHAR(255)
          email         VARCHAR(255)
          city          VARCHAR(100)
          created_at    TIMESTAMP WITH TIME ZONE

    Args:
        engine:  SQLAlchemy engine connected to the target database.
        db_name: Label used in the header comment (e.g. "sales_db").

    Returns:
        Multi-line string describing all tables and their columns.
    """
    inspector = sa_inspect(engine)
    lines: list[str] = []

    if db_name:
        lines.append(f"-- {db_name} schema")

    for table_name in sorted(inspector.get_table_names()):
        lines.append(f"Table: {table_name}")
        columns = inspector.get_columns(table_name)
        for col in columns:
            col_type = str(col["type"])
            nullable = "" if col.get("nullable", True) else " NOT NULL"
            lines.append(f"  {col['name']:<24}{col_type}{nullable}")

        # Include foreign keys if present
        fks = inspector.get_foreign_keys(table_name)
        for fk in fks:
            referred = f"{fk['referred_table']}.{', '.join(fk['referred_columns'])}"
            local = ", ".join(fk["constrained_columns"])
            lines.append(f"  -- FK: {local} -> {referred}")

        lines.append("")  # blank line between tables

    return "\n".join(lines).rstrip()


def get_schema_for_prompt(
    engines: dict[str, Engine],
) -> str:
    """Return combined schema for multiple databases, ready for an LLM prompt.

    Args:
        engines: Mapping of db_name -> Engine, e.g.
                 {"sales_db": sales_engine, "inventory_db": inv_engine}

    Returns:
        Combined schema string with a section per database.
    """
    sections: list[str] = []
    for db_name, engine in engines.items():
        sections.append(get_schema(engine, db_name=db_name))
    return "\n\n".join(sections)
