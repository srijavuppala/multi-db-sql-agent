"""
Phase 2 — DATA-03 tests.
Verifies: inventory.db tables exist with correct columns.
Requires: inventory.db seeded (skips gracefully if not).
"""
from sqlalchemy import inspect, text


def test_tables_exist(inventory_engine):
    """DATA-03: products, stock_levels, suppliers tables exist."""
    inspector = inspect(inventory_engine)
    existing = set(inspector.get_table_names())
    required = {"products", "stock_levels", "suppliers"}
    missing = required - existing
    assert not missing, f"Missing tables in inventory_db: {missing}"


def test_products_columns(inventory_engine):
    """DATA-03: products table has product_id, name, category, unit_price, supplier_id."""
    inspector = inspect(inventory_engine)
    cols = {c["name"] for c in inspector.get_columns("products")}
    required = {"product_id", "name", "category", "unit_price", "supplier_id"}
    missing = required - cols
    assert not missing, f"products table missing columns: {missing}"


def test_stock_levels_columns(inventory_engine):
    """DATA-03: stock_levels table has product_id, quantity_on_hand, reorder_threshold, last_updated."""
    inspector = inspect(inventory_engine)
    cols = {c["name"] for c in inspector.get_columns("stock_levels")}
    required = {"product_id", "quantity_on_hand", "reorder_threshold", "last_updated"}
    missing = required - cols
    assert not missing, f"stock_levels table missing columns: {missing}"


def test_suppliers_columns(inventory_engine):
    """DATA-03: suppliers table has supplier_id, name, contact_name, country."""
    inspector = inspect(inventory_engine)
    cols = {c["name"] for c in inspector.get_columns("suppliers")}
    required = {"supplier_id", "name", "contact_name", "country"}
    missing = required - cols
    assert not missing, f"suppliers table missing columns: {missing}"
