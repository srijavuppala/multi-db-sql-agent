"""Phase 6 — AGENT-08: synthesizer_node tests (LLM mocked)."""
from unittest.mock import MagicMock, patch

from src.agent.nodes.synthesizer import synthesizer_node


def _mock_llm(answer: str):
    resp = MagicMock()
    resp.content = answer
    llm = MagicMock()
    llm.invoke.return_value = resp
    return llm


@patch("src.agent.nodes.synthesizer.get_llm")
def test_synthesizer_returns_final_answer(mock_get_llm):
    mock_get_llm.return_value = _mock_llm("There are 42 customers.")

    result = synthesizer_node({
        "question": "How many customers?",
        "sql": "SELECT COUNT(*) FROM customers",
        "result": [{"count": 42}],
    })

    assert "final_answer" in result
    assert result["final_answer"] == "There are 42 customers."


@patch("src.agent.nodes.synthesizer.get_llm")
def test_synthesizer_returns_error_message_when_no_results(mock_get_llm):
    mock_get_llm.return_value = _mock_llm("irrelevant")

    result = synthesizer_node({
        "question": "Q",
        "error": "column does not exist",
        "result": [],
        "results_by_db": {},
    })

    assert "unable" in result["final_answer"].lower() or "error" in result["final_answer"].lower()
    mock_get_llm.return_value.invoke.assert_not_called()  # LLM not called on total failure


@patch("src.agent.nodes.synthesizer.get_llm")
def test_synthesizer_handles_multi_db_results(mock_get_llm):
    mock_get_llm.return_value = _mock_llm("Alice ordered 3 low-stock items.")

    result = synthesizer_node({
        "question": "Which customers ordered low-stock products?",
        "sql_by_db": {
            "sales_db": "SELECT customer_id, product_id FROM orders",
            "inventory_db": "SELECT product_id FROM stock_levels WHERE quantity_on_hand < reorder_threshold",
        },
        "results_by_db": {
            "sales_db": [{"customer_id": 1, "product_id": 101}],
            "inventory_db": [{"product_id": 101}],
        },
    })

    assert result["final_answer"] == "Alice ordered 3 low-stock items."


@patch("src.agent.nodes.synthesizer.get_llm")
def test_synthesizer_only_returns_final_answer_key(mock_get_llm):
    mock_get_llm.return_value = _mock_llm("Answer.")

    result = synthesizer_node({
        "question": "Q",
        "sql": "SELECT 1",
        "result": [{"val": 1}],
    })

    assert set(result.keys()) == {"final_answer"}
