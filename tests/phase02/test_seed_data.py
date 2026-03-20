"""
Phase 2 — DATA-04 and DATA-05 tests.
Verifies: product_id overlap with PRODUCT_IDS, row counts, low-stock condition.
Requires: inventory.db seeded (skips gracefully if not).
"""
from sqlalchemy import text
from constants import PRODUCT_IDS


def test_product_count(inventory_engine):
    """DATA-05: products table has exactly 10 rows."""
    with inventory_engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM products")).scalar()
    assert count == 10, f"Expected 10 products, got {count}"


def test_product_id_overlap(inventory_engine):
    """DATA-04: All product_id values in inventory_db match PRODUCT_IDS (101-110)."""
    with inventory_engine.connect() as conn:
        rows = conn.execute(text("SELECT product_id FROM products ORDER BY product_id")).fetchall()
    inventory_pids = {r[0] for r in rows}
    expected = set(PRODUCT_IDS)
    assert inventory_pids == expected, (
        f"Inventory product_ids {sorted(inventory_pids)} do not match "
        f"PRODUCT_IDS {sorted(expected)}"
    )


def test_suppliers_count(inventory_engine):
    """DATA-05: suppliers table has between 3 and 5 rows."""
    with inventory_engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM suppliers")).scalar()
    assert 3 <= count <= 5, f"Expected 3-5 suppliers, got {count}"


def test_stock_levels_count(inventory_engine):
    """DATA-05: stock_levels table has exactly 10 rows (one per product)."""
    with inventory_engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM stock_levels")).scalar()
    assert count == 10, f"Expected 10 stock_level rows, got {count}"


def test_low_stock_products_exist(inventory_engine):
    """DATA-05 / demo query: At least 4 products have quantity_on_hand < reorder_threshold."""
    with inventory_engine.connect() as conn:
        result = conn.execute(text(
            "SELECT COUNT(*) FROM stock_levels "
            "WHERE quantity_on_hand < reorder_threshold"
        )).scalar()
    assert result >= 4, (
        f"Expected at least 4 low-stock products, got {result}. "
        "Demo query requires low-stock items to return interesting results."
    )


def test_inventory_queryable_raw_sqlalchemy(inventory_engine):
    """DATA-05: Raw SQLAlchemy SELECT returns results from inventory_db."""
    with inventory_engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT p.name, s.quantity_on_hand "
            "FROM products p "
            "JOIN stock_levels s ON p.product_id = s.product_id "
            "LIMIT 1"
        )).fetchall()
    assert len(rows) == 1, "Expected at least 1 row from JOIN query — inventory_db not queryable"
