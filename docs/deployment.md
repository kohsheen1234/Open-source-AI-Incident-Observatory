# Deployment & observability

The whole system comes up with a single command, behind a Caddy reverse proxy, with
Prometheus scraping the API and Grafana visualising it.

## One command

```bash
make up      # docker compose up -d --build
```

This builds the application image and starts six services on one network:

| Service | What it is | Reachable at |
|---|---|---|
| **db** | PostgreSQL 16 | host `localhost:5433` (internal `db:5432`) |
| **api** | FastAPI (runs `alembic upgrade head` on start, then serves) | via Caddy at `/api` |
| **dashboard** | Streamlit review UI | via Caddy at `/` |
| **prometheus** | Scrapes `api:8000/metrics` every 15s | internal |
| **grafana** | Provisioned dashboard + Prometheus datasource | via Caddy at `/grafana` (anonymous view enabled) |
| **caddy** | Reverse proxy (auto-HTTPS in production) | `http://localhost:8080` |

Then browse **http://localhost:8080** for the dashboard and
**http://localhost:8080/grafana** for the metrics.

Tear it down with `make down` (add `-v` manually to drop the data volume).

## Populating it

The application image includes the CLI, so you can drive collection and
classification inside the running stack:

```bash
docker compose -f deploy/docker-compose.yml exec api \
  sh -c "agentwatch collect --source replay && agentwatch classify --provider baseline"
```

The dashboard, `/api/stats`, and the Grafana panels update immediately.

## Metrics

The API exposes Prometheus metrics at `/metrics`, derived from the database (so they
are correct even though collection and serving run in different processes):

- `agentwatch_incidents_total`
- `agentwatch_classifications_total`
- `agentwatch_abstention_rate`
- `agentwatch_incidents_by_type{incident_type="…"}`
- `agentwatch_collection_runs_total{status="…"}`

Prometheus scrapes these; the provisioned Grafana dashboard ("AgentWatch") plots them.

## Local open-weight models (optional)

Ollama is defined under a compose profile so the default stack needs no model server:

```bash
docker compose -f deploy/docker-compose.yml --profile llm up -d
docker compose -f deploy/docker-compose.yml exec ollama ollama pull qwen2.5:7b-instruct
```

Then classify with `--provider ollama` (point the app at `http://ollama:11434` via
`AGENTWATCH_OLLAMA_HOST`).

## Hosted options

- **Documentation site** — published automatically to GitHub Pages by the
  [`docs` workflow](https://github.com/kohsheen1234/Open-source-AI-Incident-Observatory/actions/workflows/docs.yml)
  on every push to `main`:
  <https://kohsheen1234.github.io/Open-source-AI-Incident-Observatory/>.
- **Interactive app (one click)** — the [`render.yaml`](https://github.com/kohsheen1234/Open-source-AI-Incident-Observatory/blob/main/render.yaml)
  blueprint provisions the API, the dashboard, and a managed Postgres on
  [Render](https://render.com). The app connects to a `postgres://` URL, which
  AgentWatch normalises to a psycopg3 SQLAlchemy URL automatically.

## Deploying to a VPS with HTTPS

1. Provision a small VPS (e.g. Hetzner/DigitalOcean) with Docker installed, and point
   a DNS record at it.
2. Edit `deploy/Caddyfile` — replace `:80` with your hostname:
   ```caddyfile
   observatory.example.org {
       handle_path /api/* { reverse_proxy api:8000 }
       handle_path /grafana/* { reverse_proxy grafana:3000 }
       handle { reverse_proxy dashboard:8501 }
   }
   ```
   Caddy obtains and renews Let's Encrypt certificates automatically — no extra config.
3. Set real secrets (`AGENTWATCH_API_KEY`, a strong `GF_SECURITY_ADMIN_PASSWORD`,
   Postgres credentials) via environment or an `.env` file.
4. `make up`, then schedule collection with `agentwatch schedule` (or a cron/systemd
   timer invoking `agentwatch collect`).

!!! note "Scope"
    This is a lean, reproducible deployment suited to the project's current scale.
    Hardening for production (managed Postgres, backups, secret management, horizontal
    scaling) is intentionally out of scope and would be the next step.
