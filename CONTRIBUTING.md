# Contributing

Thanks for your interest in AgentWatch.

## Development setup

```bash
pip install -e ".[dev]"
make test
```

See [`docs/development.md`](docs/development.md) for the full guide, including how to
run PostgreSQL and add schema changes.

## Ground rules

- **Tests first.** Every change comes with a test, and the suite must stay green
  (`make test`). Tests run on SQLite and need no external services.
- **Lint clean.** Run `make lint` (`ruff`) before opening a pull request.
- **Small, focused commits.** Each commit should do one thing and explain why.
- **Keep modules focused.** Each module has a single responsibility; if a file starts
  doing too much, split it.
- **Respect the data model's principles.** Raw evidence stays immutable and hashed;
  author identifiers are only ever stored as salted hashes.

## Schema changes

Schema changes go through Alembic — never edit the database by hand. See the
"Adding a schema change" section of the development guide.
