"""Pydantic request / response models for the FastAPI backend."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Natural-language question")


class QueryResponse(BaseModel):
    question: str
    final_answer: str
    db_targets: list[str] | None = None
    # Single-DB
    sql: str | None = None
    result: list[dict[str, Any]] | None = None
    # Multi-DB
    sql_by_db: dict[str, str] | None = None
    results_by_db: dict[str, list[dict[str, Any]]] | None = None
    # Execution metadata
    error: str | None = None
    retry_count: int | None = None
