# Multi-DB SQL Agent

An agentic text-to-SQL system that lets you ask natural language questions across multiple databases and get correct, sourced SQL answers. Built with LangGraph, FastAPI, and React.

## What it does

Ask a question like:

> "Show me the top 5 customers by revenue, and which of those have low-stock items?"

The agent:
1. Routes the question to the correct database(s)
2. Injects the relevant schema into context
3. Generates SQL via an LLM
4. Executes the query — and self-corrects on errors (up to 3 retries)
5. Synthesizes results from multiple DBs when needed
6. Returns the answer + the SQL it ran

## Architecture

```
User question (natural language)
        ↓
   [Router Node]         — decides: sales_db? inventory_db? both?
        ↓
   [Schema Injector]     — injects only the relevant schema
        ↓
   [SQL Generator Node]  — LLM writes SQL for the target DB
        ↓
   [SQL Executor]        — runs it, catches errors
        ↓  (on error, loops back up to 3x)
   [Self-Correction]     — feeds error back to LLM to rewrite SQL
        ↓
   [Synthesizer]         — merges cross-DB results in Python
        ↓
   Answer + SQL in React UI
```

## Databases

| Database | Engine | Purpose |
|----------|--------|---------|
| `sales_db` | Postgres 17 | Customers, orders, order items |
| `inventory_db` | SQLite | Products, stock levels |

Both share `PRODUCT_IDS` (101–110) as the cross-DB join key.

## Tech Stack

- **Agent orchestration** — LangGraph
- **LLM** — Claude (Anthropic) or OpenAI (configurable)
- **Backend** — FastAPI
- **Frontend** — React (chat UI + schema sidebar + SQL display)
- **Databases** — Postgres 17 (Docker), SQLite
- **ORM / DB access** — SQLAlchemy with psycopg3
- **SQL validation** — sqlglot (AST-level, blocks mutations before execution)
- **Testing** — pytest

## Project Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Postgres Sales DB | Complete |
| 2 | SQLite Inventory DB | Complete |
| 3 | LLM Abstraction & DB Tools | Pending |
| 4 | SQL Generation Node | Pending |
| 5 | Self-Correction Loop | Pending |
| 6 | Routing, Cross-DB & Memory | Pending |
| 7 | FastAPI Backend | Pending |
| 8 | React Frontend | Pending |

## Getting Started

### Prerequisites

- Docker + Docker Compose
- Python 3.13+
- [uv](https://github.com/astral-sh/uv)

### Setup

```bash
# 1. Clone and enter the project
cd multi-db-sql-agent

# 2. Copy and fill in environment variables
cp .env.example .env

# 3. Start Postgres
docker compose up --wait

# 4. Install dependencies
uv sync

# 5. Seed the databases
uv run python db/seeds/seed_sales_db.py
uv run python db/seeds/seed_inventory_db.py

# 6. Run tests
uv run pytest
```

## Security

- Postgres uses a read-only role (`app_readonly`) — INSERT/UPDATE/DELETE/DROP are rejected at the DB level
- All SQL is validated via `sqlglot` AST analysis before execution — mutations are blocked before they reach the database

## Environment Variables

| Variable | Description |
|----------|-------------|
| `POSTGRES_PASSWORD` | Postgres superuser password |
| `SALES_DB_READONLY_URL` | `postgresql+psycopg://app_readonly:...@localhost:5432/sales_db` |
| `SALES_DB_ADMIN_URL` | `postgresql+psycopg://postgres:...@localhost:5432/sales_db` |
| `INVENTORY_DB_URL` | `sqlite:///./db/inventory.db` |
| `ANTHROPIC_API_KEY` | Claude API key (Phase 3+) |
| `OPENAI_API_KEY` | OpenAI API key (optional, Phase 3+) |
