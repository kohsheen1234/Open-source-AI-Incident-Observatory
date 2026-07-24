# API & dashboard

AgentWatch exposes its incidents through a documented HTTP API, and ships a React (Vite + TypeScript + Tailwind)
dashboard that consumes that API. The dashboard never touches the database directly —
everything goes through the same API an external consumer would use.

## Running the API

```bash
agentwatch serve --host 127.0.0.1 --port 8000
```

FastAPI serves interactive OpenAPI docs at `/docs` and the raw schema at
`/openapi.json`.

## Endpoints

| Method & path | Purpose |
|---|---|
| `GET /health` | Liveness check |
| `GET /incidents` | List incidents; filters: `source`, `incident_type`, `abstained`, `min_severity`; pagination: `limit` (1–500), `offset` |
| `GET /incidents/{id}` | Incident detail: body, all classifications, and reviews |
| `POST /incidents/{id}/review` | Record a human review of the latest classification |
| `GET /stats` | Totals, per-type counts, and abstention rate |
| `GET /exports/incidents.csv` | Export incidents (with latest classification) as CSV |

### Listing incidents

```bash
curl "http://localhost:8000/incidents?incident_type=deception&limit=20"
```

Response is a page:

```json
{
  "items": [
    {
      "id": 12,
      "source": "hackernews",
      "url": "https://news.ycombinator.com/item?id=...",
      "title": "...",
      "published_at": "...",
      "ingested_at": "...",
      "classification": {
        "incident_type": "deception",
        "relevance": "relevant",
        "severity": 3,
        "confidence": 0.7,
        "abstained": false,
        "model_name": "baseline",
        "prompt_version": "v1"
      }
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### Recording a review

```bash
curl -X POST "http://localhost:8000/incidents/12/review" \
  -H "Content-Type: application/json" \
  -d '{"reviewer": "alice", "decision": "accept", "notes": "clear first-party report"}'
```

`decision` is one of `accept`, `override`, or `false_positive`. The review is attached
to the incident's most recent classification, preserving the machine label alongside
the human judgement.

## Authentication

Read endpoints are public. **If `AGENTWATCH_API_KEY` is set**, write endpoints
(`POST .../review`) and the CSV export require a matching `X-API-Key` header:

```bash
curl -X POST ".../review" -H "X-API-Key: $AGENTWATCH_API_KEY" -H "Content-Type: application/json" -d '...'
```

When the variable is unset, authentication is disabled — so a reviewer can run the
whole thing locally with zero configuration, while a production deployment can lock
writes down by setting the key.

## The dashboard

The dashboard is a **React single-page app** (Vite + TypeScript + Tailwind, Recharts)
in `frontend/`, deployed as a static site and served locally by Caddy in the compose
stack. To run just the frontend against a local API:

```bash
agentwatch serve                                 # API on :8000, in one terminal
cd frontend && npm install
VITE_API_URL=http://localhost:8000 npm run dev   # web on :5173, in another
```

Three pages:

- **Overview** — headline metrics (incidents, classified, abstention rate) and an
  incidents-by-type chart.
- **Incident Explorer** — a filterable table of incidents and their latest
  classification.
- **Review Queue** — open an incident, read its evidence and classification, and submit
  an accept / override / false-positive decision.

Because the dashboard talks only to the API, the same API backs both human review and
any external/automated consumer.
