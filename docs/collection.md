# Collecting data

AgentWatch collects public reports from pluggable **sources**, preserves each as
tamper-evident evidence, and turns them into de-duplicated **incidents** in the
database. This page covers the sources that exist today and how to run collection.

## The pipeline

```text
  source.fetch(since)          →  list of RawArtifact (in memory)
        │
        ▼
  for each artifact:
    content_hash already seen?  →  yes: skip (de-duplicate)
        │ no
        ▼
    write evidence to disk      →  <artifact_dir>/<source>/<year>/<month>/<sha256>.json
    insert raw_artifacts row    →  the verbatim original + hash
    insert incidents row        →  normalised; author stored as a salted hash
        │
        ▼
  record a collection_runs row  →  status, items fetched, items new, any error
```

The whole run is wrapped so that **one source failing never stops the others** — its
failure is recorded on its own `collection_runs` row and collection continues.

## Sources

Every source implements a single interface:

```python
class DataSource(Protocol):
    name: str
    def fetch(self, since: datetime) -> list[RawArtifact]: ...
```

Adding a new source means writing one class that implements `fetch`. The three that
exist today:

| Source | Live? | Credentials | Notes |
|---|---|---|---|
| **replay** | fixtures | none | Bundled sample incidents. The credential-free default, so the pipeline runs end-to-end out of the box. |
| **hackernews** | yes | none | Live via the public Hacker News (Algolia) search API. |
| **reddit** | yes | required | Opt-in. Enabled only when Reddit API credentials are set. |

### Replay

The replay source reads a bundled JSON fixture of representative incident reports.
Because it needs no network or credentials, it is what makes the system fully runnable
by anyone who clones the repository.

### Hacker News

Queries the Hacker News Algolia API for stories matching a set of AI-agent-incident
search terms, and maps each hit to a `RawArtifact`. HTTP calls retry with exponential
backoff on transient network errors.

### Reddit (opt-in)

Disabled unless both `AGENTWATCH_REDDIT_CLIENT_ID` and
`AGENTWATCH_REDDIT_CLIENT_SECRET` are set. Install the optional dependency with
`pip install -e ".[reddit]"`.

## Running collection

```bash
# One-off, from a single source
agentwatch collect --source replay
agentwatch collect --source hackernews --since-hours 168

# One-off, from every configured source (Reddit included only if enabled)
agentwatch collect --source all

# Continuously, on a fixed interval
agentwatch schedule --interval-minutes 60
```

`--since-hours` controls how far back to look; collection is incremental and
idempotent, so running it repeatedly is safe.

## Evidence preservation

Every collected item is written to disk verbatim, in a path derived from its source,
date, and **SHA-256 content hash**:

```text
<AGENTWATCH_ARTIFACT_DIR>/<source>/<year>/<month>/<sha256>.json
```

Because the filename *is* the content hash, the same item is only ever stored once,
and any later change to the content would produce a different hash — so tampering is
detectable and the original evidence survives even if the source post is deleted.
