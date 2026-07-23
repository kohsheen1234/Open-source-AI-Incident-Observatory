# AgentWatch

**An open-source observatory for public reports of AI-agent incidents.**

AI systems increasingly act on their own — running tools, taking actions, and
operating with growing autonomy. When they behave in unexpected or unintended ways,
people write about it: an agent that deleted the wrong files, ignored an instruction,
took an action nobody approved, or behaved deceptively. Those reports are scattered
across forums and social platforms, and the original posts often disappear.

AgentWatch exists to turn that scattered, disappearing evidence into a durable,
searchable, and analysable record.

![AgentWatch demo](assets/demo.gif)

!!! info "Project status"
    The end-to-end pipeline is built and runnable today: the data foundation, the
    ingestion pipeline (pluggable collectors, evidence storage, normalisation,
    scheduled collection), the classification + evaluation layer (pluggable
    abstain-capable classifier, labelled eval set, regression gate), the web layer
    (documented authenticated HTTP API + Streamlit review dashboard), and observability
    + deployment (Prometheus metrics, a provisioned Grafana dashboard, and a one-command
    `docker compose` stack behind Caddy). Nothing here is aspirational.

## Why separate raw evidence from interpretation?

The core design principle is that **the original evidence and any interpretation of
it are kept apart**:

- A **raw artifact** is the source record, stored verbatim and hashed. It is never
  edited. If the original post is deleted, the evidence remains; if it is altered, the
  hash no longer matches.
- An **incident** is the cleaned-up, de-duplicated version used for analysis.
- A **classification** is a machine's *opinion* about an incident — always attributed
  to a specific model and prompt version, so it can be reproduced and audited.
- A **review** is a *human's* decision about a classification.

This separation means every conclusion can be traced back to the exact evidence it
came from, and you always know whether a label came from a machine or a person.

## Where to go next

- **[Architecture](architecture.md)** — the components that exist today and how they
  fit together.
- **[Collecting data](collection.md)** — the sources, the pipeline, and how to run it.
- **[Classification & evaluation](classification.md)** — the taxonomy, providers, and how quality is measured.
- **[API & dashboard](api.md)** — the HTTP API, authentication, and the review dashboard.
- **[Deployment & observability](deployment.md)** — one-command stack, metrics, and VPS/HTTPS.
- **[Data model](data-model.md)** — the full, table-by-table schema reference.
- **[Development](development.md)** — how to install, test, and extend the project.
