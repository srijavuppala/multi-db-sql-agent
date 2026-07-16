"""Phase 7 — API tests (graph and DB calls mocked)."""
from unittest.mock import patch, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.app import app
from src.api.models import QueryRequest, QueryResponse


# ── Model validation ──────────────────────────────────────────────────────────

def test_query_request_requires_question():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        QueryRequest()


def test_query_request_rejects_empty_string():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        QueryRequest(question="")


def test_query_response_model():
    resp = QueryResponse(
        question="How many customers?",
        final_answer="There are 5 customers.",
        db_targets=["sales_db"],
        sql="SELECT COUNT(*) FROM customers",
        result=[{"count": 5}],
    )
    assert resp.final_answer == "There are 5 customers."
    assert resp.error is None


# ── Health endpoint ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── /query endpoint ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("src.api.app.build_graph")
async def test_query_endpoint_returns_answer(mock_build_graph):
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {
        "question": "How many customers?",
        "final_answer": "There are 5 customers.",
        "db_targets": ["sales_db"],
        "sql": "SELECT COUNT(*) FROM customers",
        "result": [{"count": 5}],
        "error": None,
        "retry_count": 0,
    }
    mock_build_graph.return_value = mock_graph

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/query", json={"question": "How many customers?"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["final_answer"] == "There are 5 customers."
    assert body["db_targets"] == ["sales_db"]


@pytest.mark.asyncio
@patch("src.api.app.build_graph")
async def test_query_endpoint_rejects_empty_question(mock_build_graph):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/query", json={"question": ""})
    assert resp.status_code == 422


@pytest.mark.asyncio
@patch("src.api.app.build_graph")
async def test_query_endpoint_handles_graph_exception(mock_build_graph):
    mock_graph = MagicMock()
    mock_graph.invoke.side_effect = RuntimeError("LLM unavailable")
    mock_build_graph.return_value = mock_graph

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/query", json={"question": "Any question"})

    assert resp.status_code == 500
