"""
LangGraph agent graph (Phase 5 — self-correction loop).

Graph topology
--------------

    START
      │
      ▼
  generate_sql  ◄────────────────────────┐
      │                                  │  retry
      ▼                                  │
  execute_sql ──► should_retry ──► "retry" (retry_count < 3 and error)
                        │
                        └──► "done"  (success OR retries exhausted)
                                │
                               END

Nodes
-----
  generate_sql  — sql_generation_node  (src/agent/nodes/sql_generator.py)
  execute_sql   — executor_node        (src/agent/nodes/executor.py)

Conditional edge
----------------
  should_retry()  returns "retry" → back to generate_sql (correction prompt)
                  returns "done"  → END

Usage
-----
    from src.agent.graph import build_graph

    graph = build_graph()
    result = graph.invoke({
        "question": "How many customers are in NYC?",
        "schema": "...",
        "db_targets": ["sales_db"],
    })
    print(result["sql"])
    print(result["result"])
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from src.agent.nodes.executor import executor_node, should_retry
from src.agent.nodes.sql_generator import sql_generation_node
from src.agent.state import AgentState

# Node name constants — avoids magic strings across tests
NODE_GENERATE = "generate_sql"
NODE_EXECUTE = "execute_sql"


def build_graph() -> StateGraph:
    """Compile and return the LangGraph agent graph.

    Returns:
        A compiled LangGraph runnable (supports .invoke() and .stream()).
    """
    builder = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────
    builder.add_node(NODE_GENERATE, sql_generation_node)
    builder.add_node(NODE_EXECUTE, executor_node)

    # ── Entry point ───────────────────────────────────────────────────────
    builder.add_edge(START, NODE_GENERATE)

    # ── Generate → Execute (always) ───────────────────────────────────────
    builder.add_edge(NODE_GENERATE, NODE_EXECUTE)

    # ── Execute → retry or done ───────────────────────────────────────────
    builder.add_conditional_edges(
        NODE_EXECUTE,
        should_retry,
        {
            "retry": NODE_GENERATE,   # loop back with error in state
            "done": END,
        },
    )

    return builder.compile()
