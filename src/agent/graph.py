"""
LangGraph agent graph (Phase 6 — full pipeline).

Graph topology
--------------

    START
      │
      ▼
    router          — keyword-based DB classification
      │
      ▼
    schema_inject   — fetch schemas for targeted DB(s)
      │
      ▼
    generate_sql  ◄──────────────────────────────┐
      │                                          │  retry (error + retries < 3)
      ▼                                          │
    execute_sql ──► should_retry ──► "retry" ───┘
                          │
                          └──► "done"
                                  │
                                  ▼
                            synthesize      — LLM generates final_answer
                                  │
                                 END

Nodes
-----
  router         — router_node          (nodes/router.py)
  schema_inject  — schema_injector_node (nodes/schema_injector.py)
  generate_sql   — sql_generation_node  (nodes/sql_generator.py)
  execute_sql    — executor_node        (nodes/executor.py)
  synthesize     — synthesizer_node     (nodes/synthesizer.py)

Usage
-----
    from src.agent.graph import build_graph

    graph = build_graph()
    result = graph.invoke({"question": "Who are the top 5 customers by revenue?"})
    print(result["final_answer"])
    print(result["sql"])
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from src.agent.nodes.executor import executor_node, should_retry
from src.agent.nodes.router import router_node
from src.agent.nodes.schema_injector import schema_injector_node
from src.agent.nodes.sql_generator import sql_generation_node
from src.agent.nodes.synthesizer import synthesizer_node
from src.agent.state import AgentState

NODE_ROUTER = "router"
NODE_SCHEMA = "schema_inject"
NODE_GENERATE = "generate_sql"
NODE_EXECUTE = "execute_sql"
NODE_SYNTHESIZE = "synthesize"


def build_graph():
    """Compile and return the full LangGraph agent pipeline.

    Returns:
        A compiled LangGraph runnable (supports .invoke() and .stream()).
    """
    builder = StateGraph(AgentState)

    builder.add_node(NODE_ROUTER, router_node)
    builder.add_node(NODE_SCHEMA, schema_injector_node)
    builder.add_node(NODE_GENERATE, sql_generation_node)
    builder.add_node(NODE_EXECUTE, executor_node)
    builder.add_node(NODE_SYNTHESIZE, synthesizer_node)

    builder.add_edge(START, NODE_ROUTER)
    builder.add_edge(NODE_ROUTER, NODE_SCHEMA)
    builder.add_edge(NODE_SCHEMA, NODE_GENERATE)
    builder.add_edge(NODE_GENERATE, NODE_EXECUTE)
    builder.add_conditional_edges(
        NODE_EXECUTE,
        should_retry,
        {
            "retry": NODE_GENERATE,
            "done": NODE_SYNTHESIZE,
        },
    )
    builder.add_edge(NODE_SYNTHESIZE, END)

    return builder.compile()
