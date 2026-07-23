# Data model

AgentWatch's schema has five tables. They form a chain from raw evidence to human
judgement, keeping the original record separate from every interpretation of it.

```text
collection_runs ──< raw_artifacts ──< incidents ──< classifications ──< reviews
```

All timestamps are stored timezone-aware, in UTC.

---

## `collection_runs`

One row per collection job. Records what ran and how it went, so a gap or failure in
collection is visible rather than silent.

| Column | Type | Notes |
|---|---|---|
| `id` | int | Primary key |
| `source` | str(50) | Which source the run collected from (indexed) |
| `started_at` | datetime | When the run began |
| `finished_at` | datetime? | When it ended (null while running) |
| `status` | str(30) | `running` / `success` / `failed` |
| `items_fetched` | int | How many records were pulled |
| `items_new` | int | How many were new (not already stored) |
| `error` | text? | Failure detail, if any |

## `raw_artifacts`

The untouched source record. **This is the evidence** — it is written once and never
edited.

| Column | Type | Notes |
|---|---|---|
| `id` | int | Primary key |
| `source` | str(50) | Origin platform (indexed) |
| `source_id` | str(255) | The record's ID on that platform |
| `url` | text | Link to the original |
| `content_hash` | str(64) | **SHA-256** of the content — unique, indexed |
| `raw_json` | JSONB | The full original payload, verbatim |
| `fetched_at` | datetime | When it was collected |
| `collection_run_id` | int? | The run that fetched it |

The unique `content_hash` is what makes collection **idempotent**: re-collecting the
same content inserts nothing new, and any later change to the content is detectable
because the hash won't match.

## `incidents`

The normalised, de-duplicated report used for analysis. Derived from a raw artifact.

| Column | Type | Notes |
|---|---|---|
| `id` | int | Primary key |
| `raw_artifact_id` | int | The evidence this came from |
| `source` | str(50) | Origin platform (indexed) |
| `url` | text | Link to the original |
| `title` | text | Report title |
| `body` | text | Report text |
| `author_hash` | str(64)? | **Salted hash** of the author — never plaintext |
| `published_at` | datetime? | When the report was published |
| `ingested_at` | datetime | When AgentWatch normalised it |
| `content_hash` | str(64) | Unique, indexed — dedupe key |

There is deliberately **no raw-author column**. Author identity only ever exists as a
salted hash.

## `classifications`

A machine's label for an incident. An incident can have several classifications (for
example, from different models), so each is attributed to the exact model and prompt
that produced it.

| Column | Type | Notes |
|---|---|---|
| `id` | int | Primary key |
| `incident_id` | int | The incident labelled (indexed) |
| `model_name` | str(100) | Which model produced the label |
| `prompt_version` | str(50) | Which prompt version was used |
| `relevance` | str(50) | Whether the incident is in-scope |
| `incident_type` | str(50) | The category assigned |
| `severity` | int? | Severity rating |
| `evidence_quality` | str(50)? | How well-supported the report is |
| `autonomy_level` | str(50)? | How autonomous the system was |
| `confidence` | float | The model's confidence |
| `abstained` | bool | True when the model declined to label |
| `reasoning_summary` | text? | Short rationale |
| `cost_usd` | float | Cost of the call |
| `latency_ms` | int | Time the call took |
| `created_at` | datetime | When the label was made |

Recording `model_name` and `prompt_version` on every row means any classification can
be reproduced and compared as models and prompts change.

## `reviews`

A human's decision about a classification — the point where a person accepts,
corrects, or rejects what the machine said.

| Column | Type | Notes |
|---|---|---|
| `id` | int | Primary key |
| `classification_id` | int | The classification reviewed (indexed) |
| `reviewer` | str(100) | Who reviewed it |
| `decision` | str(30) | `accept` / `override` / `false_positive` |
| `corrected_fields` | JSONB? | Any fields the reviewer changed |
| `notes` | text? | Reviewer notes |
| `reviewed_at` | datetime | When it was reviewed |

Keeping human decisions in their own table — rather than editing the machine's
classification in place — preserves both the original machine label and the human
correction, which is exactly what you need to measure how well the classifier is
doing.
