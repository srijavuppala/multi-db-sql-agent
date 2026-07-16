"""
Router Node (Phase 6).

Classifies the user's question and sets db_targets to indicate which
database(s) should be queried.

Uses keyword matching — deterministic, fast, no API call needed. The
keywords are tuned for the sales_db / inventory_db domain described in
the project README.

Rules
-----
- If the question mentions customer/order/revenue keywords → sales_db
- If the question mentions product/stock/inventory keywords → inventory_db
- If BOTH keyword sets match → both databases
- If neither matches → default to sales_db

Usage:
    from src.agent.nodes.router import router_node
    patch = router_node({"question": "Which products are low on stock?"})
    # -> {"db_targets": ["inventory_db"]}
"""
from __future__ import annotations

import re

from src.agent.state import AgentState

_SALES_KEYWORDS: frozenset[str] = frozenset({
    "customer", "customers", "order", "orders", "revenue", "revenues",
    "purchase", "purchases", "sale", "sales", "spend", "spending",
    "payment", "payments", "buyer", "buyers", "invoice", "invoices",
    "total", "amount", "city", "email",
})

_INVENTORY_KEYWORDS: frozenset[str] = frozenset({
    "product", "products", "stock", "stocks", "inventory", "inventories",
    "supplier", "suppliers", "warehouse", "quantity", "quantities",
    "reorder", "restock", "item", "items", "low", "out-of-stock",
    "unit_price", "category", "categories",
})


def _tokenise(text: str) -> set[str]:
    """Lower-case and split text into word tokens."""
    return set(re.findall(r"[a-z_]+", text.lower()))


def router_node(state: AgentState) -> AgentState:
    """LangGraph node — classify question and set db_targets.

    Reads from state:
        question — the user's natural-language question

    Writes to state:
        db_targets — ["sales_db"], ["inventory_db"], or both

    Returns:
        Partial AgentState dict with db_targets set.
    """
    question = state.get("question", "")
    tokens = _tokenise(question)

    has_sales = bool(tokens & _SALES_KEYWORDS)
    has_inventory = bool(tokens & _INVENTORY_KEYWORDS)

    if has_sales and has_inventory:
        db_targets = ["sales_db", "inventory_db"]
    elif has_inventory:
        db_targets = ["inventory_db"]
    else:
        db_targets = ["sales_db"]  # default — most questions are sales-oriented

    return {"db_targets": db_targets}
