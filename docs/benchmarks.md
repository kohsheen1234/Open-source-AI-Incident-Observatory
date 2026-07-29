# Benchmarks & failure modes

AgentWatch is a **portfolio system**: the goal is to show it's *designed and validated*
for scale, not to pay to *operate* at scale. Operating at scale needs money, users, and
time; designing for it can be shown locally, for free. This page does that — a repeatable
local load test, an honest bottleneck, and deliberate-failure tests.

## Reproduce it

```bash
agentwatch bench --count 100000 --duplicate-fraction 0.3
```

It generates synthetic incidents, runs them through the **real** ingestion and
classification pipeline on a throwaway SQLite database, then measures API latency
in-process. No credentials, no cloud, no cost.

## Results

Workload: **100,000** synthetic incidents, **30% duplicates**, single process, SQLite,
on a developer laptop.

| Stage | Metric | Result |
|---|---|---|
| Ingestion | throughput | **~4,100 records/sec** (24.2 s total) |
| Ingestion | dedup suppression | **30,000 / 100,000 (30%)** correctly skipped |
| Classification (baseline) | throughput | **~8,600 incidents/sec** (8.2 s total) |
| API `GET /incidents` | p50 / p95 | **188 ms / 204 ms** (70k rows, 200 samples) |
| Footprint | database size | **64.5 MB** |
| Footprint | peak memory | **~266 MB** |

### The bottleneck: list-endpoint latency

Ingestion and classification are comfortably fast. The clear bottleneck is
**`GET /incidents` at ~188 ms p50** once the table holds 70k rows. The cause is the query
shape, not the row count:

- it builds a **"latest classification per incident"** subquery (`GROUP BY … MAX(id)`)
  and outer-joins it, then
- runs a **full `COUNT(*)` over that joined subquery** on every request to populate
  `total`.

On SQLite with no supporting index for that access pattern, both scale with the table.

**How I'd fix it (in priority order):**

1. **Keyset (cursor) pagination** instead of `LIMIT/OFFSET` + full count — O(page), not
   O(table). Return an opaque `next` cursor rather than a global `total`.
2. **Materialise the latest classification** — a `latest_classification_id` column on
   `incidents` maintained at classify time — removes the per-request `GROUP BY` join.
3. **Postgres + a covering index** on `classifications(incident_id, id)` and
   `incidents(id)` — the production database, not SQLite.
4. **Cache `/stats`** (small, changes slowly) behind a short TTL / CDN.

Each is a real change with a tradeoff (e.g. keyset pagination trades a global `total` for
speed), which is the point: the benchmark tells you *where* to spend effort before you
spend money.

## Failure modes (tested)

Each of these is a passing test in `tests/test_failure_modes.py` — a fault is injected and
the system's response is asserted:

| Injected fault | Behaviour |
|---|---|
| A collector **times out / raises** | Failure is isolated to that source's `collection_run` (recorded `failed`); other sources still succeed. |
| **Storage fails mid-batch** | The run is **atomic** — its ingested rows roll back, so no partial data is committed; the run is recorded `failed`. |
| **Duplicate collection** (same content re-ingested) | Idempotent — content-hash dedupe inserts nothing new (`items_new = 0`). |
| **Malformed / empty source text** | Ingests without crashing; the classifier **abstains** (`insufficient_evidence`). |
| **Classifier returns unparseable output** | Retried once, then **abstains** — never persists an invalid label. |

The atomicity guarantee comes from a deliberate design choice: ingestion runs in its own
transaction (rolled back on failure) while the `collection_run` record is written in a
separate transaction, so a failed run is always recorded *and* leaves no partial data.

## What this demonstrates

Defining a workload, measuring it, locating the bottleneck, and proposing the fix with its
tradeoff — plus failure-aware design validated by tests — is the signal that matters more
than an expensive cloud deployment.
