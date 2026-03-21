"""
Seed script for SQLite inventory_db.

Creates schema (DDL) and inserts deterministic seed data.
No Faker — inventory is static reference data (10 products, 3-5 suppliers).

Usage (from project root: langgraph/):
    uv run python multi-db-sql-agent/db/seeds/seed_inventory_db.py

CRITICAL: product_id values come exclusively from PRODUCT_IDS in constants.py.
DO NOT use random integers — they must match sales_db.order_items.product_id for
Phase 6 cross-DB queries.
"""
import sys
import os

# Ensure src/ and seeds/ are importable when run from project root
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_agent_root = os.path.join(_project_root, "multi-db-sql-agent")
_seeds_root = os.path.join(_agent_root, "db", "seeds")

for _path in [_project_root, _agent_root, _seeds_root]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from sqlalchemy import text

# Import from constants.py — DO NOT duplicate or copy-paste PRODUCT_IDS
from constants import PRODUCT_IDS
from src.db.connections import get_inventory_engine, verify_connection


# ── Seed data ─────────────────────────────────────────────────────────────────

SUPPLIERS = [
    {"supplier_id": 1, "name": "TechSupply Co",        "contact_name": "Alice Chen",   "country": "USA"},
    {"supplier_id": 2, "name": "GlobalComponents Ltd",  "contact_name": "James Park",   "country": "South Korea"},
    {"supplier_id": 3, "name": "EuroTech GmbH",         "contact_name": "Marta Vogel",  "country": "Germany"},
    {"supplier_id": 4, "name": "Pacific Peripherals",   "contact_name": "Hiro Tanaka",  "country": "Japan"},
]

# 10 products — product_id values are PRODUCT_IDS[0..9] = 101..110
PRODUCTS = [
    {"product_id": PRODUCT_IDS[0], "name": "Wireless Keyboard",          "category": "Peripherals",  "unit_price": 79.99,  "supplier_id": 1},
    {"product_id": PRODUCT_IDS[1], "name": "USB-C Hub 7-Port",           "category": "Accessories",  "unit_price": 49.99,  "supplier_id": 2},
    {"product_id": PRODUCT_IDS[2], "name": "Mechanical Mouse",           "category": "Peripherals",  "unit_price": 59.99,  "supplier_id": 1},
    {"product_id": PRODUCT_IDS[3], "name": "Noise-Cancelling Headphones","category": "Audio",        "unit_price": 149.99, "supplier_id": 3},
    {"product_id": PRODUCT_IDS[4], "name": "Webcam 1080p",               "category": "Video",        "unit_price": 89.99,  "supplier_id": 2},
    {"product_id": PRODUCT_IDS[5], "name": "Laptop Stand Aluminium",     "category": "Accessories",  "unit_price": 39.99,  "supplier_id": 4},
    {"product_id": PRODUCT_IDS[6], "name": "Portable SSD 1TB",          "category": "Storage",      "unit_price": 119.99, "supplier_id": 3},
    {"product_id": PRODUCT_IDS[7], "name": "HDMI 2.1 Cable 2m",         "category": "Cables",       "unit_price": 19.99,  "supplier_id": 4},
    {"product_id": PRODUCT_IDS[8], "name": "27-inch Monitor 4K",         "category": "Displays",     "unit_price": 349.99, "supplier_id": 2},
    {"product_id": PRODUCT_IDS[9], "name": "Ergonomic Wrist Rest",       "category": "Accessories",  "unit_price": 24.99,  "supplier_id": 1},
]

# quantity_on_hand < reorder_threshold = LOW STOCK (marked with # LOW)
# At least 4 products must be low-stock for the Phase 6 demo query to return results.
STOCK_LEVELS = [
    {"product_id": PRODUCT_IDS[0], "quantity_on_hand": 8,   "reorder_threshold": 25,  "last_updated": "2025-01-10"},  # LOW
    {"product_id": PRODUCT_IDS[1], "quantity_on_hand": 150, "reorder_threshold": 50,  "last_updated": "2025-01-15"},
    {"product_id": PRODUCT_IDS[2], "quantity_on_hand": 12,  "reorder_threshold": 30,  "last_updated": "2025-01-20"},  # LOW
    {"product_id": PRODUCT_IDS[3], "quantity_on_hand": 200, "reorder_threshold": 40,  "last_updated": "2025-02-01"},
    {"product_id": PRODUCT_IDS[4], "quantity_on_hand": 7,   "reorder_threshold": 20,  "last_updated": "2025-02-05"},  # LOW
    {"product_id": PRODUCT_IDS[5], "quantity_on_hand": 80,  "reorder_threshold": 30,  "last_updated": "2025-02-10"},
    {"product_id": PRODUCT_IDS[6], "quantity_on_hand": 5,   "reorder_threshold": 15,  "last_updated": "2025-02-15"},  # LOW
    {"product_id": PRODUCT_IDS[7], "quantity_on_hand": 300, "reorder_threshold": 100, "last_updated": "2025-03-01"},
    {"product_id": PRODUCT_IDS[8], "quantity_on_hand": 3,   "reorder_threshold": 10,  "last_updated": "2025-03-05"},  # LOW
    {"product_id": PRODUCT_IDS[9], "quantity_on_hand": 90,  "reorder_threshold": 40,  "last_updated": "2025-03-10"},
]


def create_schema(engine) -> None:
    """Create tables if they do not exist. Safe to re-run (idempotent DDL)."""
    with engine.begin() as conn:
        # Enable FK enforcement for this connection
        conn.execute(text("PRAGMA foreign_keys = ON"))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS suppliers (
                supplier_id   INTEGER PRIMARY KEY,
                name          TEXT NOT NULL,
                contact_name  TEXT NOT NULL,
                country       TEXT NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                product_id   INTEGER PRIMARY KEY,
                name         TEXT NOT NULL,
                category     TEXT NOT NULL,
                unit_price   REAL NOT NULL,
                supplier_id  INTEGER NOT NULL
                             REFERENCES suppliers(supplier_id)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stock_levels (
                product_id         INTEGER PRIMARY KEY
                                   REFERENCES products(product_id),
                quantity_on_hand   INTEGER NOT NULL,
                reorder_threshold  INTEGER NOT NULL,
                last_updated       TEXT NOT NULL
            )
        """))
    print("Schema created (or already exists).")


def seed(engine) -> None:
    """Clear tables and insert deterministic seed data."""
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))
        # Delete in FK-safe order (children before parents)
        conn.execute(text("DELETE FROM stock_levels"))
        conn.execute(text("DELETE FROM products"))
        conn.execute(text("DELETE FROM suppliers"))

        # Insert suppliers
        for s in SUPPLIERS:
            conn.execute(text(
                "INSERT INTO suppliers (supplier_id, name, contact_name, country) "
                "VALUES (:supplier_id, :name, :contact_name, :country)"
            ), s)

        # Insert products
        for p in PRODUCTS:
            conn.execute(text(
                "INSERT INTO products (product_id, name, category, unit_price, supplier_id) "
                "VALUES (:product_id, :name, :category, :unit_price, :supplier_id)"
            ), p)

        # Insert stock levels
        for sl in STOCK_LEVELS:
            conn.execute(text(
                "INSERT INTO stock_levels (product_id, quantity_on_hand, reorder_threshold, last_updated) "
                "VALUES (:product_id, :quantity_on_hand, :reorder_threshold, :last_updated)"
            ), sl)

    low_stock_count = sum(
        1 for sl in STOCK_LEVELS if sl["quantity_on_hand"] < sl["reorder_threshold"]
    )
    print(f"  Inserted {len(SUPPLIERS)} suppliers")
    print(f"  Inserted {len(PRODUCTS)} products")
    print(f"  Inserted {len(STOCK_LEVELS)} stock_level rows ({low_stock_count} low-stock)")
    print("Seed complete.")


if __name__ == "__main__":
    print("Connecting to inventory_db (SQLite) ...")
    engine = get_inventory_engine()

    if not verify_connection(engine):
        # SQLite auto-creates the file; this check confirms the path is writable
        print("WARNING: Could not connect — check INVENTORY_DB_URL and directory permissions.")

    print("Creating schema ...")
    create_schema(engine)

    print("Seeding ...")
    seed(engine)

    # Verify counts post-seed
    from sqlalchemy import text as _text
    with engine.connect() as conn:
        n_products = conn.execute(_text("SELECT COUNT(*) FROM products")).scalar()
        n_low = conn.execute(_text(
            "SELECT COUNT(*) FROM stock_levels WHERE quantity_on_hand < reorder_threshold"
        )).scalar()

    if n_products != 10:
        print(f"ERROR: Expected 10 products, got {n_products}.")
        raise SystemExit(1)

    if n_low < 4:
        print(f"ERROR: Expected >= 4 low-stock products, got {n_low}.")
        raise SystemExit(1)

    print(f"Done. {n_products} products in inventory_db ({n_low} low-stock).")
