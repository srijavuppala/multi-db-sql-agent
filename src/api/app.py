"""
FastAPI backend for the multi-db-sql-agent (Phase 7).

Endpoints
---------
POST /query  — run a natural-language question through the LangGraph agent
GET  /health — liveness check
GET  /schema — return DB schemas for the frontend sidebar

Run locally:
    uvicorn src.api.app:app --reload --port 8000
"""
from __future__ import annotations

import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.agent.graph import build_graph
from src.api.models import QueryRequest, QueryResponse
from src.db.connections import get_inventory_engine, get_sales_engine
from src.tools.schema import get_schema

app = FastAPI(
    title="Multi-DB SQL Agent",
    description="Ask natural-language questions across sales_db and inventory_db.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/schema")
async def schema() -> dict:
    """Return formatted schemas for both databases (used by the React sidebar)."""
    schemas: dict[str, str] = {}
    try:
        schemas["sales_db"] = get_schema(get_sales_engine(), db_name="sales_db")
    except Exception as exc:
        schemas["sales_db"] = f"(unavailable: {exc})"
    try:
        schemas["inventory_db"] = get_schema(get_inventory_engine(), db_name="inventory_db")
    except Exception as exc:
        schemas["inventory_db"] = f"(unavailable: {exc})"
    return schemas


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """Run a natural-language question through the LangGraph agent.

    The graph is compiled on each request (stateless). For production, consider
    compiling once at startup and sharing via dependency injection.
    """
    graph = build_graph()
    try:
        # LangGraph .invoke() is synchronous — run in a thread pool
        state = await asyncio.to_thread(
            graph.invoke,
            {"question": request.question},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return QueryResponse(
        question=request.question,
        final_answer=state.get("final_answer") or "",
        db_targets=state.get("db_targets"),
        sql=state.get("sql") or None,
        result=state.get("result") or None,
        sql_by_db=state.get("sql_by_db") or None,
        results_by_db=state.get("results_by_db") or None,
        error=state.get("error"),
        retry_count=state.get("retry_count"),
    )
