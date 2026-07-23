# AgentWatch

**An open-source observatory for public reports of AI-agent incidents.**

As AI systems increasingly act on their own — running tools, taking actions, and
operating with growing autonomy — people are posting about what happens when those
systems behave in unexpected or unintended ways: an agent that deletes the wrong
files, ignores an instruction, takes an action nobody approved, or behaves
deceptively. These reports are scattered across forums and social platforms, and
the original posts often disappear.

**AgentWatch's goal is to turn that scattered, disappearing evidence into a durable,
searchable, and analysable record** — so researchers and safety teams can measure
how often these incidents happen, what kinds occur, and how the picture changes over
time.

> ### 🔭 Project status: in active development
>
> **What exists today: the data foundation, the ingestion pipeline, and the
> classification + evaluation layer.** AgentWatch can collect public reports from
> pluggable sources, preserve each as tamper-evident hashed evidence, normalise them
> into de-duplicated incidents, and classify each incident with a pluggable,
> abstain-capable classifier whose quality is measured by a labelled evaluation set
> and a prompt-regression gate. **The monitoring dashboard and the HTTP API are
> designed but not yet implemented.** This README documents only what is actually
> built and runnable right now, and grows as each part lands.
>
> Everything described below works today. Try it in five minutes with
> [Quickstart](#quickstart).

---

## What's built today

AgentWatch is being built in layers. The foundation layer — the part that is
complete and tested — provides:

| Capability | What it does |
|---|---|
| **Typed configuration** | All settings (database, storage location, log level, secrets) load from environment variables with safe defaults, validated at startup. |
| **Structured logging** | JSON logs via `structlog`, ready for aggregation and machine parsing. |
| **Database schema** | A five-table relational model (below) that captures raw evidence, normalised incidents, machine classifications, human reviews, and collection runs. |
| **Migrations** | Versioned schema changes via Alembic; the same schema runs on PostgreSQL (production) and SQLite (fast tests). |
| **Containerised database** | A one-command PostgreSQL service via Docker Compose. |
| **Pluggable collectors** | A `DataSource` interface with three adapters: Hacker News (live), Replay (bundled fixtures, no credentials needed), and Reddit (opt-in). Adding a source is one new file. |
| **Tamper-evident evidence** | Every collected item is stored verbatim on disk, named by its SHA-256 hash, so evidence survives deletion of the original. |
| **Normalise + de-duplicate** | Collected items become de-duplicated incidents; re-collecting the same content adds nothing. Author identifiers are hashed. |
| **Reliable collection** | A CLI and optional scheduler run collection with retries, per-source failure isolation, and a recorded run history. |
| **Pluggable classifier** | An `LLMProvider` interface with three backends: a deterministic Baseline (default, no dependencies), Ollama (local open-weight models), and optional Anthropic. Structured JSON output is validated; malformed output is retried, then abstained. |
| **Abstain-capable taxonomy** | Ten incident types plus an explicit *insufficient_evidence* outcome, so the system distinguishes "no incident" from "not enough evidence". |
| **Measured quality** | A labelled evaluation set with precision / recall / macro-F1 / confusion matrix / abstention rate, and a regression test that fails if macro-F1 drops below a committed floor. |
| **Test suite** | Every component is covered by tests that run in under a second. |

If you clone this repository, all of the above runs and passes. Nothing here is a
placeholder.

## The data model

The schema is the heart of the foundation. It is designed around a simple idea:
**keep the original evidence separate from any interpretation of it**, and record who
interpreted it and how.

```text
collection_runs        — one row per collection job (when it ran, what it found, any error)
        │
        ▼
raw_artifacts          — the untouched source record + a SHA-256 content hash
        │                 (evidence is preserved even if the original is deleted)
        ▼
incidents              — the normalised, de-duplicated report (title, body, source, date)
        │                 author identifiers are stored HASHED, never in the raw
        ▼
classifications        — a machine label for an incident (type, severity, confidence…)
        │                 records the model and prompt version used
        ▼
reviews                — a human decision on a classification (accept / override / reject)
```

Two design choices worth calling out, because they shape everything downstream:

- **Raw evidence is immutable and hashed.** Every source record is stored verbatim
  with a SHA-256 hash, so the evidence survives even if the original post is removed,
  and any later tampering is detectable.
- **Author privacy by default.** Author identifiers are stored as salted hashes, never
  in plaintext. The schema has no column for a raw author name.

See [`docs/data-model.md`](docs/data-model.md) for the full table-by-table reference.

## Quickstart

**Requirements:** Python 3.12+ and Docker.

```bash
# 1. Install the package and dev tools (a virtualenv is recommended)
pip install -e ".[dev]"

# 2. Start PostgreSQL (runs on host port 5433 to avoid clashing with a local Postgres)
make db-up

# 3. Point AgentWatch at it and create the schema
cp .env.example .env
make migrate

# 4. Run the test suite
make test
```

You now have a running database with the full AgentWatch schema, verified by tests.

To run against SQLite instead (no Docker needed), leave `AGENTWATCH_DATABASE_URL`
unset — it defaults to a local SQLite file, which is exactly what the test suite uses.

## Collecting incidents

Once the schema exists, collect incidents with the `agentwatch` CLI. The **replay**
source needs no credentials and works immediately, so you can see the full pipeline
end to end:

```bash
# Collect from the bundled replay fixtures (no credentials required)
agentwatch collect --source replay

# Collect live from Hacker News, or from every configured source
agentwatch collect --source hackernews
agentwatch collect --source all --since-hours 168

# Run collection continuously on a schedule
agentwatch schedule --interval-minutes 60
```

Each run stores the original evidence under `AGENTWATCH_ARTIFACT_DIR`
(as `<source>/<year>/<month>/<sha256>.json`), writes de-duplicated incidents to the
database, and records a row in `collection_runs`. Re-running over the same window
adds nothing new.

**Sources:**

- **replay** — bundled sample incidents; the credential-free default.
- **hackernews** — live via the public Hacker News (Algolia) API; no key required.
- **reddit** — opt-in; set `AGENTWATCH_REDDIT_CLIENT_ID` and
  `AGENTWATCH_REDDIT_CLIENT_SECRET` and install the extra (`pip install -e ".[reddit]"`).

## Classifying incidents

Once incidents exist, classify the ones that have no classification yet:

```bash
# Deterministic baseline classifier (default; no model server or network needed)
agentwatch classify --provider baseline

# Classify with a local open-weight model served by Ollama
agentwatch classify --provider ollama
```

Each classification records the incident type, severity, confidence, whether the
model **abstained**, and the exact `model_name` and `prompt_version` used — so results
are reproducible and auditable.

## Measuring classifier quality

Run the labelled evaluation set and print metrics:

```bash
agentwatch eval --provider baseline
# → {"n": 24, "macro_f1": 1.0, "abstention_rate": 0.125, "total_cost_usd": 0.0, ...}
```

The same command works with `--provider ollama` to compare a real model against the
baseline on identical data. A test (`tests/test_eval.py`) runs this evaluation and
**fails if macro-F1 drops below a committed floor**, so a prompt or model change that
regresses quality is caught automatically.

See [`docs/classification.md`](docs/classification.md) for the taxonomy, the providers,
and the evaluation methodology.

## Configuration

All configuration is read from environment variables prefixed `AGENTWATCH_`
(see [`.env.example`](.env.example)):

| Variable | Default | Purpose |
|---|---|---|
| `AGENTWATCH_DATABASE_URL` | local SQLite file | SQLAlchemy database URL |
| `AGENTWATCH_ARTIFACT_DIR` | `./artifacts` | Where raw evidence files are stored |
| `AGENTWATCH_AUTHOR_HASH_SALT` | `change-me-in-production` | Salt for hashing author identifiers |
| `AGENTWATCH_LOG_LEVEL` | `INFO` | Log verbosity |
| `AGENTWATCH_ENVIRONMENT` | `local` | Deployment environment label |
| `AGENTWATCH_REDDIT_CLIENT_ID` | _(unset)_ | Enables the opt-in Reddit source |
| `AGENTWATCH_REDDIT_CLIENT_SECRET` | _(unset)_ | Enables the opt-in Reddit source |

## Tech stack

Python 3.12 · SQLAlchemy 2.0 · Alembic · Pydantic · httpx · tenacity · APScheduler ·
structlog · PostgreSQL 16 · Docker Compose · pytest · ruff.

## Documentation

Longer-form docs live in [`docs/`](docs/) and are published as a
[MkDocs](https://www.mkdocs.org/) site:

- [Overview](docs/index.md) — what AgentWatch is and how the foundation fits together
- [Architecture](docs/architecture.md) — the components that exist today
- [Data model](docs/data-model.md) — full schema reference
- [Development](docs/development.md) — setup, testing, and how to add a migration

To preview the docs site locally:

```bash
pip install -e ".[docs]"
mkdocs serve
```

## Project layout

```text
agentwatch/        # the package
  config.py        # typed settings from the environment
  logging.py       # structured JSON logging
  hashing.py       # content + author hashing
  collectors/      # DataSource protocol + adapters (hackernews, replay, reddit)
  storage/         # tamper-evident artifact file store
  pipeline/        # ingest (persist/normalise/dedupe) + collection orchestration
  classify/        # taxonomy, prompt, providers (baseline/ollama/anthropic), classifier
  eval/            # labelled dataset, metrics, evaluation runner
  sources.py       # source + provider registry / defaults
  cli.py           # `agentwatch` command-line interface
  scheduler.py     # APScheduler-based recurring collection
  db/              # SQLAlchemy models, base, portable types, session management
migrations/        # Alembic migration environment and versions
deploy/            # docker-compose service definitions
docs/              # MkDocs documentation site
tests/             # test suite
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

See [LICENSE](LICENSE).
