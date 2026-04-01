"""
Schema Injector Node (Phase 6).

Reads db_targets from state, fetches the schema for each targeted database,
and stores both the combined schema string (for the LLM prompt) and a per-DB
dict (for the multi-DB SQL generator).

Usage:
    from src.agent.nodes.schema_injector import schema_injector_node
    patch = schema_injector_node({"db_targets": ["sales_db"]})
    # -> {"schema": "-- sales_db schema\n...", "schemas_by_db": {"sales_db": "..."}}
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from src.agent.state import AgentState
from src.db.connections import get_inventory_engine, get_sales_engine
from src.tools.schema import get_schema


def _engine_for_db(db_name: str) -> Engine:
    if db_name == "sales_db":
        return get_sales_engine(readonly=True)
    if db_name == "inventory_db":
        return get_inventory_engine()
    raise ValueError(f"Unknown database: {db_name!r}")


def schema_injector_node(state: AgentState) -> AgentState:
    """LangGraph node — fetch and inject DB schemas into state.

    Reads from state:
        db_targets — list of DB names to introspect

    Writes to state:
        schema        — combined schema string (all targeted DBs)
        schemas_by_db — dict of db_name → individual schema string

    Returns:
        Partial AgentState dict with schema and schemas_by_db set.
    """
    db_targets = state.get("db_targets") or ["sales_db"]
    schemas_by_db: dict[str, str] = {}

    for db_name in db_targets:
        engine = _engine_for_db(db_name)
        schemas_by_db[db_name] = get_schema(engine, db_name=db_name)

    combined_schema = "\n\n".join(schemas_by_db.values())

    return {
        "schema": combined_schema,
        "schemas_by_db": schemas_by_db,
    }
