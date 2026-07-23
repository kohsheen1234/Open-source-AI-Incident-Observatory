# Development

## Setup

Requires **Python 3.12+** and (for PostgreSQL) **Docker**.

```bash
pip install -e ".[dev]"
```

## Running the tests

The test suite uses SQLite and needs no external services:

```bash
make test          # or: python -m pytest -q
```

It runs in about a second and covers configuration, logging, the schema, session
handling, and migrations.

## Linting

```bash
make lint          # ruff check .
```

Auto-generated Alembic migrations are excluded from linting.

## Working with the database

Start a local PostgreSQL (host port 5433) and create the schema:

```bash
make db-up
cp .env.example .env
make migrate
```

Inspect it:

```bash
docker compose -f deploy/docker-compose.yml exec db psql -U agentwatch -d agentwatch -c "\dt"
```

Stop it:

```bash
make db-down
```

## Adding a schema change

1. Edit the models in `agentwatch/db/models.py`.
2. Autogenerate a migration:
   ```bash
   alembic revision --autogenerate -m "describe the change"
   ```
3. Review the generated file in `migrations/versions/`. If it references a custom
   type (such as the portable `JSONB`), make sure the corresponding import is present.
4. Apply it:
   ```bash
   make migrate
   ```
5. Confirm the test suite still passes on SQLite:
   ```bash
   make test
   ```

## How the code is organised

| Path | Responsibility |
|---|---|
| `agentwatch/config.py` | Typed settings from the environment |
| `agentwatch/logging.py` | Structured JSON logging |
| `agentwatch/db/base.py` | SQLAlchemy declarative base |
| `agentwatch/db/types.py` | Portable `JSONB` column type |
| `agentwatch/db/models.py` | The five ORM models |
| `agentwatch/db/session.py` | Engine and `session_scope()` |
| `migrations/` | Alembic environment and versions |
| `deploy/` | Docker Compose services |
| `tests/` | Test suite |

Each module has one clear responsibility, which keeps files small and easy to test in
isolation.
