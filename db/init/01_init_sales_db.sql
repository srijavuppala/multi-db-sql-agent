-- Phase 1: sales_db initialization
-- Runs automatically via docker-entrypoint-initdb.d on first container start.
-- IMPORTANT: This script is skipped on subsequent `docker compose up` if the
-- data volume already exists. To re-run: docker compose down -v && docker compose up

-- ============================================================
-- Read-only application role (SEC-02, DATA-06)
-- ============================================================

-- Create the read-only role that all application code will use.
-- Password must match APP_READONLY_PASSWORD in .env
CREATE ROLE app_readonly WITH LOGIN PASSWORD 'changeme_readonly';

-- Grant connection to the sales_db database
GRANT CONNECT ON DATABASE sales_db TO app_readonly;

-- Grant usage of the public schema
GRANT USAGE ON SCHEMA public TO app_readonly;

-- ============================================================
-- Table DDL (DATA-01)
-- ============================================================

CREATE TABLE customers (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    email       VARCHAR(255) UNIQUE NOT NULL,
    city        VARCHAR(100),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE orders (
    id           SERIAL PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(id),
    order_date   DATE NOT NULL,
    status       VARCHAR(50) NOT NULL DEFAULT 'completed',
    total_amount NUMERIC(10, 2) NOT NULL
);

CREATE TABLE order_items (
    id         SERIAL PRIMARY KEY,
    order_id   INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL,   -- Soft FK to SQLite inventory_db (app-level only)
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL
);

-- ============================================================
-- Grant SELECT on all tables to app_readonly (SEC-02)
-- CRITICAL: This must come AFTER all CREATE TABLE statements.
-- ALTER DEFAULT PRIVILEGES covers future tables; this covers existing ones.
-- ============================================================

GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO app_readonly;
