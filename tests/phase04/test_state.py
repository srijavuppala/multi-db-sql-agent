"""
Phase 4 — AGENT-01 tests.
Verifies: AgentState TypedDict structure and field defaults.
"""
from src.agent.state import AgentState


def test_state_accepts_question():
    """AGENT-01: AgentState can be constructed with just a question."""
    state: AgentState = {"question": "How many customers are there?"}
    assert state["question"] == "How many customers are there?"


def test_state_accepts_all_fields():
    """AGENT-01: AgentState accepts all defined fields."""
    state: AgentState = {
        "question": "Top 5 customers?",
        "db_targets": ["sales_db"],
        "schema": "Table: customers\n  id INTEGER\n  name TEXT",
        "sql": "SELECT id, name FROM customers LIMIT 5",
        "error": None,
        "retry_count": 0,
        "result": [{"id": 1, "name": "Alice"}],
        "final_answer": "The top customer is Alice.",
    }
    assert state["db_targets"] == ["sales_db"]
    assert state["retry_count"] == 0
    assert state["error"] is None


def test_state_is_partial():
    """AGENT-01: AgentState fields are all optional (total=False)."""
    # Should not raise — all fields are optional
    state: AgentState = {}
    assert state == {}
