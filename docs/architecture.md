# Architecture

This page describes the components that exist **today**. As new layers (collection,
classification, dashboard, API) are built, they will be documented here.

## The foundation layer

```text
  environment variables
          │
          ▼
   ┌──────────────┐        ┌──────────────────┐
   │  Settings    │        │  Structured      │
   │  (config.py) │        │  logging         │
   │  validated   │        │  (structlog,     │
   │  at startup  │        │   JSON output)   │
   └──────┬───────┘        └──────────────────┘
          │
          ▼
   ┌──────────────────────────────────────────┐
   │  Database layer (agentwatch/db)            │
   │                                            │
   │  models.py   — 5 SQLAlchemy 2.0 models     │
   │  base.py     — declarative base            │
   │  types.py    — portable JSONB type         │
   │  session.py  — engine + session_scope()    │
   └──────┬─────────────────────────────────────┘
          │
          ▼
   ┌──────────────┐   applied by   ┌──────────────┐
   │  Alembic     │───────────────▶│  PostgreSQL  │  (Docker Compose)
   │  migrations  │                │  or SQLite   │  (tests)
   └──────────────┘                └──────────────┘
```

## Components

### Configuration (`agentwatch/config.py`)

A single `Settings` object, built on `pydantic-settings`, reads every setting from
`AGENTWATCH_`-prefixed environment variables and validates them at startup. A cached
`get_settings()` accessor gives the rest of the code one consistent source of truth.
There is no configuration scattered through the codebase.

### Logging (`agentwatch/logging.py`)

Logging is configured once, centrally, and emits **structured JSON** via `structlog`.
Structured logs are machine-parseable, which matters for a system whose whole purpose
is turning messy input into analysable records. `get_logger(name)` returns a bound
logger anywhere in the code.

### Database layer (`agentwatch/db/`)

- **`models.py`** defines the five tables (see [Data model](data-model.md)) using
  SQLAlchemy 2.0's typed `Mapped[...]` style.
- **`types.py`** provides a portable `JSONB` column type: real `JSONB` on PostgreSQL,
  and generic `JSON` on SQLite. This is what lets the identical schema run in
  production and in fast unit tests.
- **`session.py`** exposes `session_scope()`, a context manager that commits on
  success and rolls back on error, so callers never leak transactions.

### Migrations (`migrations/`)

Schema changes are versioned with Alembic. The initial migration creates all five
tables. Because migrations use Alembic's batch mode, they apply cleanly on both
PostgreSQL and SQLite.

### Containerised database (`deploy/docker-compose.yml`)

A PostgreSQL 16 service with a health check, mapped to host port **5433** (chosen to
avoid clashing with a Postgres already running locally on 5432). `make db-up` starts
it; `make migrate` creates the schema.

## Portability: PostgreSQL and SQLite

A deliberate design goal is that the same schema and code run on two databases:

- **PostgreSQL** in real use, for concurrency and native JSONB.
- **SQLite** in the test suite, so tests need no external services and run in under a
  second.

The portable `JSONB` type and Alembic batch migrations are what make this work.
