"""
Seed script for Postgres sales_db.

Generates realistic fake data using Faker with seed 42 for reproducibility.
Expected output: ~30 customers, ~120 orders, ~300 order_items.

Usage (from project root after `docker compose up --wait`):
    uv run python multi-db-sql-agent/db/seeds/seed_sales_db.py

CRITICAL: product_id values come exclusively from PRODUCT_IDS in constants.py.
DO NOT use random integers — they must match inventory_db for Phase 6 cross-DB queries.
"""
import sys
import os
import random

# Ensure src/ and seeds/ are importable when running from project root
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_agent_root = os.path.join(_project_root, "multi-db-sql-agent")
_seeds_root = os.path.join(_agent_root, "db", "seeds")

for _path in [_project_root, _agent_root, _seeds_root]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from faker import Faker
from sqlalchemy import text

# Import from constants.py — DO NOT duplicate or copy-paste PRODUCT_IDS
from constants import PRODUCT_IDS
from src.db.connections import get_sales_engine, wait_for_db

# ── Reproducibility ──────────────────────────────────────────────────────────
fake = Faker()
Faker.seed(42)
random.seed(42)

# ── Volume parameters ─────────────────────────────────────────────────────────
NUM_CUSTOMERS = 30
NUM_ORDERS_PER_CUSTOMER_RANGE = (2, 6)   # avg 4 orders/customer → ~120 orders
NUM_ITEMS_PER_ORDER_RANGE = (1, 4)       # avg 2.5 items/order → ~300 order_items

ORDER_STATUSES = ["completed", "shipped", "pending", "cancelled"]


def seed(engine) -> None:
    """Truncate tables and insert fresh seed data."""
    with engine.begin() as conn:
        # Truncate in FK-safe order (child → parent)
        conn.execute(text(
            "TRUNCATE order_items, orders, customers RESTART IDENTITY CASCADE"
        ))

        # ── Insert customers ──────────────────────────────────────────────────
        customer_ids: list[int] = []
        for _ in range(NUM_CUSTOMERS):
            result = conn.execute(
                text(
                    "INSERT INTO customers (name, email, city) "
                    "VALUES (:name, :email, :city) RETURNING id"
                ),
                {
                    "name": fake.name(),
                    "email": fake.unique.email(),
                    "city": fake.city(),
                },
            )
            customer_ids.append(result.scalar_one())

        print(f"  Inserted {len(customer_ids)} customers")

        # ── Insert orders and order_items ─────────────────────────────────────
        total_orders = 0
        total_items = 0

        for cid in customer_ids:
            n_orders = random.randint(*NUM_ORDERS_PER_CUSTOMER_RANGE)
            for _ in range(n_orders):
                total_amount = round(random.uniform(20.0, 500.0), 2)
                order_result = conn.execute(
                    text(
                        "INSERT INTO orders (customer_id, order_date, status, total_amount) "
                        "VALUES (:cid, :date, :status, :total) RETURNING id"
                    ),
                    {
                        "cid": cid,
                        "date": fake.date_between(start_date="-2y", end_date="today"),
                        "status": random.choice(ORDER_STATUSES),
                        "total": total_amount,
                    },
                )
                order_id = order_result.scalar_one()
                total_orders += 1

                n_items = random.randint(*NUM_ITEMS_PER_ORDER_RANGE)
                for _ in range(n_items):
                    qty = random.randint(1, 5)
                    price = round(random.uniform(5.0, 150.0), 2)
                    conn.execute(
                        text(
                            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
                            "VALUES (:oid, :pid, :qty, :price)"
                        ),
                        {
                            "oid": order_id,
                            # CRITICAL: use only PRODUCT_IDS values (101-110)
                            "pid": random.choice(PRODUCT_IDS),
                            "qty": qty,
                            "price": price,
                        },
                    )
                    total_items += 1

        print(f"  Inserted {total_orders} orders")
        print(f"  Inserted {total_items} order_items")

    print("Seed complete.")
    return total_items


if __name__ == "__main__":
    print("Connecting to sales_db (admin role) ...")
    engine = get_sales_engine(readonly=False)
    wait_for_db(engine)

    print("Seeding ...")
    n_items = seed(engine)

    if n_items < 100:
        print(f"WARNING: Only {n_items} order_items inserted. Expected >= 100.")
        sys.exit(1)

    print(f"Done. {n_items} order_items in sales_db.")
