"""
Shared constants for database seeding.

CRITICAL: PRODUCT_IDS must be imported from this file by ALL seed scripts.
DO NOT copy-paste this list into other files — any divergence silently breaks
the cross-DB demo query in Phase 6.

Phase 1 (seed_sales_db.py) and Phase 2 (seed_inventory_db.py) both import PRODUCT_IDS.
"""

# Product IDs that exist in BOTH databases.
# sales_db.order_items.product_id references these values.
# inventory_db.products.product_id uses these as primary keys.
# Range: 101-110 (10 products). Integers chosen for SQL readability.
PRODUCT_IDS: list[int] = [101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
