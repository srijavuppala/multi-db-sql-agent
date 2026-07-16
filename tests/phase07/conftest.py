"""Fixtures for Phase 7 API tests."""
import sys, os
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

import pytest
from httpx import ASGITransport, AsyncClient
from src.api.app import app

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
