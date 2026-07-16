"""
Phase 5 — AGENT-04 tests.
Verifies: executor_node and should_retry behaviour (DB calls mocked).
"""
from unittest.mock import MagicMock, patch

import pytest

from src.agent.nodes.executor import _engine_for_target, executor_node, should_retry
from src.agent.state import AgentState


# ── _engine_for_target ────────────────────────────────────────────────────────

def test_engine_for_target_unknown_raises():
    """AGENT-04: Unknown db name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown db target"):
        _engine_for_target("unknown_db")


# ── executor_node — success path ──────────────────────────────────────────────

@patch("src.agent.nodes.executor.execute_query")
@patch("src.agent.nodes.executor.get_sales_engine")
def test_executor_success_returns_result(mock_engine, mock_exec):
    """AGENT-04: Successful execution returns result rows and clears error."""
    mock_exec.return_value = [{"id": 1, "name": "Alice"}]

    state: AgentState = {
        "sql": "SELECT id, name FROM customers",
        "db_targets": ["sales_db"],
        "retry_count": 0,
    }
    patch_dict = executor_node(state)

    assert patch_dict["result"] == [{"id": 1, "name": "Alice"}]
    assert patch_dict["error"] is None


@patch("src.agent.nodes.executor.execute_query")
@patch("src.agent.nodes.executor.get_sales_engine")
def test_executor_success_only_updates_result_and_error(mock_engine, mock_exec):
    """AGENT-04: Executor patch only contains 'result' and 'error' on success."""
    mock_exec.return_value = []

    state: AgentState = {
        "sql": "SELECT 1",
        "db_targets": ["sales_db"],
        "retry_count": 1,
    }
    patch_dict = executor_node(state)

    assert set(patch_dict.keys()) == {"result", "error"}


# ── executor_node — failure path ──────────────────────────────────────────────

@patch("src.agent.nodes.executor.execute_query")
@patch("src.agent.nodes.executor.get_sales_engine")
def test_executor_failure_returns_error(mock_engine, mock_exec):
    """AGENT-04: Failed execution returns error message."""
    mock_exec.side_effect = ValueError("column 'foo' does not exist")

    state: AgentState = {
        "sql": "SELECT foo FROM customers",
        "db_targets": ["sales_db"],
        "retry_count": 0,
    }
    patch_dict = executor_node(state)

    assert "foo" in patch_dict["error"]


@patch("src.agent.nodes.executor.execute_query")
@patch("src.agent.nodes.executor.get_sales_engine")
def test_executor_failure_increments_retry_count(mock_engine, mock_exec):
    """AGENT-04: Failed execution increments retry_count by 1."""
    mock_exec.side_effect = Exception("some db error")

    state: AgentState = {
        "sql": "SELECT bad FROM customers",
        "db_targets": ["sales_db"],
        "retry_count": 1,
    }
    patch_dict = executor_node(state)

    assert patch_dict["retry_count"] == 2


@patch("src.agent.nodes.executor.execute_query")
@patch("src.agent.nodes.executor.get_inventory_engine")
def test_executor_uses_inventory_engine_for_inventory_db(mock_inv_engine, mock_exec):
    """AGENT-04: Executor calls get_inventory_engine for inventory_db target."""
    mock_exec.return_value = []

    state: AgentState = {
        "sql": "SELECT * FROM products",
        "db_targets": ["inventory_db"],
        "retry_count": 0,
    }
    executor_node(state)

    mock_inv_engine.assert_called_once()


# ── should_retry ──────────────────────────────────────────────────────────────

def test_should_retry_returns_retry_on_error_with_retries_left():
    """AGENT-04: should_retry returns 'retry' when error exists and count < 3."""
    state: AgentState = {"error": "syntax error", "retry_count": 1}
    assert should_retry(state) == "retry"


def test_should_retry_returns_done_on_success():
    """AGENT-04: should_retry returns 'done' when no error."""
    state: AgentState = {"error": None, "retry_count": 0}
    assert should_retry(state) == "done"


def test_should_retry_returns_done_when_retries_exhausted():
    """AGENT-04: should_retry returns 'done' when retry_count reaches 3."""
    state: AgentState = {"error": "still failing", "retry_count": 3}
    assert should_retry(state) == "done"


def test_should_retry_returns_done_when_count_exceeds_max():
    """AGENT-04: should_retry returns 'done' when retry_count > 3."""
    state: AgentState = {"error": "still failing", "retry_count": 5}
    assert should_retry(state) == "done"


def test_should_retry_returns_retry_at_count_zero():
    """AGENT-04: should_retry returns 'retry' on the very first failure."""
    state: AgentState = {"error": "first error", "retry_count": 0}
    assert should_retry(state) == "retry"
