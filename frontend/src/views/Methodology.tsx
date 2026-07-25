import { INCIDENT_TYPES } from "../theme";
import { Card, Eyebrow, SectionHeader, TypeBadge } from "../ui";

// Each pipeline stage, described end-to-end so nothing about the workflow is opaque.
const STAGES: {
  n: string;
  name: string;
  input: string;
  transform: string;
  output: string;
  why: string;
}[] = [
  {
    n: "01",
    name: "Collect",
    input:
      "Public posts from source APIs — Hacker News (Algolia search API, live), Reddit (PRAW, opt-in), and a bundled replay sample. Original format: JSON returned by each API.",
    transform:
      "For each source we run a fixed set of AI-agent search terms (e.g. “AI agent deleted”, “autonomous agent”, “agent ignored instructions”) and map every hit into a common RawArtifact shape: source, source_id, url, title, body, author, published_at, and the untouched raw JSON. Network calls retry with exponential backoff; one source failing never aborts the others.",
    output: "A list of RawArtifact objects in memory, plus a recorded collection run.",
    why: "Incident reports are scattered across platforms and often deleted. Pulling them into one normalized shape is the first step to measuring them.",
  },
  {
    n: "02",
    name: "Preserve",
    input: "Each RawArtifact from collection.",
    transform:
      "A SHA-256 content hash is computed over a canonical form of {source, source_id, url, title, body}. The verbatim raw JSON is written to disk at <source>/<year>/<month>/<hash>.json, and a raw_artifacts row stores the original payload + hash. Author identifiers are replaced by a salted SHA-256 hash — the raw author name is never stored.",
    output: "Immutable, content-addressed evidence files + raw_artifacts rows.",
    why: "Evidence must survive even if the original post is deleted, and any later change is detectable because the hash won’t match. Author hashing is a privacy-conscious default.",
  },
  {
    n: "03",
    name: "Normalise & de-duplicate",
    input: "Raw artifacts + their content hashes.",
    transform:
      "The content hash is the dedupe key: if an artifact with that hash already exists, it is skipped, so re-collecting the same window inserts nothing new. New artifacts become incidents (title, body, url, source, hashed author, published/ingested timestamps).",
    output: "De-duplicated incidents ready to classify.",
    why: "Idempotent ingestion means the numbers you see reflect distinct reports, not re-runs.",
  },
  {
    n: "04",
    name: "Classify",
    input: "An incident’s title + body (text only).",
    transform:
      "A versioned prompt asks a pluggable classifier for a single structured JSON object. The output is validated against a schema; malformed output is retried once, then the result abstains. Every classification records the exact model_name and prompt_version, plus confidence, cost, and latency.",
    output:
      "A classifications row: relevance, incident_type, severity (1–5), evidence_quality, autonomy_level, confidence, a short reasoning summary, and an abstained flag.",
    why: "Turning free text into a consistent, attributable label is what makes incidents countable and comparable over time.",
  },
  {
    n: "05",
    name: "Evaluate",
    input: "A hand-labelled dataset of example reports shipped in the repo.",
    transform:
      "The classifier runs over the labelled set; precision, recall, macro-F1, a confusion matrix, and the abstention rate are computed. A test asserts macro-F1 stays above a committed floor.",
    output: "Quality metrics per provider, and a CI gate.",
    why: "Without measurement, a prompt or model change could silently degrade quality. The gate makes regressions fail CI.",
  },
  {
    n: "06",
    name: "Review",
    input: "A machine classification + the original evidence.",
    transform:
      "A human accepts, overrides, or flags the label as a false positive. The review is stored in its own table — the machine label is never overwritten.",
    output: "A reviews row linked to the classification.",
    why: "Machine labels are opinions. Keeping both the machine label and the human decision is exactly what lets us measure how trustworthy the classifier is.",
  },
];

const DATA_SOURCES = [
  ["Hacker News", "Algolia search API (live, no key)", "JSON hits", "title, text, author, url, created_at, raw"],
  ["Reddit", "PRAW (opt-in, needs API keys)", "submission objects", "title, selftext, author, permalink, created_utc"],
  ["Replay", "bundled fixtures in the repo", "JSON array", "a small, representative sample so it runs with no keys"],
];

const DOES = [
  "Reads only the report’s title and body (plain text).",
  "Returns a structured label: type, severity, confidence, and a one-line rationale.",
  "Abstains (insufficient_evidence) when the text isn’t clear enough to decide.",
  "Records which model and prompt version produced each label, so it’s reproducible.",
];

const DOESNT = [
  "Does not verify whether the report is true — it classifies the claim, not reality.",
  "Does not visit the original link or use anything beyond the provided text.",
  "Does not decide what gets published — a human review step exists for that.",
  "Is not authoritative: the default provider is a transparent keyword baseline, not a large model.",
];

const PROVIDERS = [
  ["Baseline", "Deterministic keyword rules. No network, no model server — the default, and what CI uses so results are reproducible."],
  ["Ollama", "A local open-weight model (e.g. Qwen/Llama) via Ollama. No API cost; runs on your own machine."],
  ["Anthropic", "An optional hosted model, with per-token cost accounting. Off unless configured."],
];

export function Methodology() {
  return (
    <div className="space-y-24">
      {/* Why */}
      <section>
        <Eyebrow>Why this exists</Eyebrow>
        <h1 className="font-extralight uppercase text-4xl md:text-6xl leading-[1.05] tracking-[0.01em] mt-3">
          <span className="grad-text">No black boxes.</span>
          <br />
          <span className="text-ink">Every step, explained.</span>
        </h1>
        <div className="mt-8 max-w-3xl space-y-4 text-muted leading-relaxed">
          <p>
            As AI systems act more autonomously, real-world reports of them misbehaving — deleting
            files, ignoring instructions, escalating their own access — are scattered across
            forums and frequently disappear. AgentWatch collects those reports, preserves them as
            tamper-evident evidence, classifies them into a consistent taxonomy, and routes
            uncertain cases to human review.
          </p>
          <p>
            This page documents the entire workflow end to end: where the data comes from, its
            original format, every transformation applied, what the classifier does and does not
            do, how the categories were chosen, and why each stage exists. Nothing here is a
            black box.
          </p>
        </div>
      </section>

      {/* Architecture diagram */}
      <section>
        <SectionHeader eyebrow="Architecture" title="The whole system at a glance" />
        <Card className="p-4 md:p-6">
          <img
            src="/architecture.svg"
            alt="AgentWatch architecture: sources → ingestion → storage → classify & evaluate → access"
            className="w-full h-auto"
            loading="lazy"
          />
        </Card>
      </section>

      {/* Pipeline stages */}
      <section>
        <SectionHeader eyebrow="The pipeline" title="From a public post to a reviewed incident" />
        <div className="space-y-4">
          {STAGES.map((s) => (
            <Card key={s.n} className="p-6">
              <div className="flex flex-col md:flex-row md:items-baseline gap-2 md:gap-4">
                <div className="font-mono text-brand text-sm tracking-[0.2em]">{s.n}</div>
                <h3 className="font-light uppercase text-2xl text-ink tracking-[0.02em]">{s.name}</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mt-5">
                <Field label="Input" value={s.input} />
                <Field label="Transformation" value={s.transform} />
                <Field label="Output" value={s.output} />
                <Field label="Why it matters" value={s.why} accent />
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Data sources */}
      <section>
        <SectionHeader eyebrow="Provenance" title="Where the data comes from, and in what format" />
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left font-mono text-[0.66rem] uppercase tracking-[0.12em] text-faint border-b border-border">
                  <th className="px-5 py-3">Source</th>
                  <th className="px-5 py-3">Access method</th>
                  <th className="px-5 py-3">Original format</th>
                  <th className="px-5 py-3">What we keep</th>
                </tr>
              </thead>
              <tbody>
                {DATA_SOURCES.map((r) => (
                  <tr key={r[0]} className="border-b border-border/60">
                    <td className="px-5 py-3 text-ink">{r[0]}</td>
                    <td className="px-5 py-3 text-muted">{r[1]}</td>
                    <td className="px-5 py-3 text-muted">{r[2]}</td>
                    <td className="px-5 py-3 text-muted">{r[3]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </section>

      {/* Classifier does / doesn't */}
      <section>
        <SectionHeader eyebrow="The classifier" title="What the LLM does — and what it doesn’t" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-6">
            <div className="font-mono text-brand text-xs uppercase tracking-[0.18em]">Does</div>
            <ul className="mt-4 space-y-2.5 text-sm text-muted">
              {DOES.map((d) => (
                <li key={d} className="flex gap-2.5">
                  <span className="text-brand">→</span>
                  {d}
                </li>
              ))}
            </ul>
          </Card>
          <Card className="p-6">
            <div className="font-mono text-[#ce2f00] text-xs uppercase tracking-[0.18em]">Does not</div>
            <ul className="mt-4 space-y-2.5 text-sm text-muted">
              {DOESNT.map((d) => (
                <li key={d} className="flex gap-2.5">
                  <span className="text-[#ce2f00]">×</span>
                  {d}
                </li>
              ))}
            </ul>
          </Card>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          {PROVIDERS.map(([name, desc]) => (
            <Card key={name} className="p-5">
              <div className="text-ink font-medium">{name}</div>
              <p className="text-sm text-muted mt-1.5 leading-relaxed">{desc}</p>
            </Card>
          ))}
        </div>
        <p className="text-sm text-muted mt-4 leading-relaxed max-w-3xl">
          The prompt is <span className="text-ink">versioned</span>, and the model must return a
          single JSON object matching a fixed schema. Invalid output is retried once, then the
          result <span className="text-ink">abstains</span> rather than guess. Because every row
          records its model and prompt version, any label can be reproduced or compared as the
          model and prompt evolve.
        </p>
      </section>

      {/* Taxonomy */}
      <section>
        <SectionHeader eyebrow="The taxonomy" title="How the categories were chosen, and why" />
        <p className="text-muted leading-relaxed max-w-3xl mb-6">
          The categories are drawn from the AI-safety literature on agentic risk and loss of
          control — the behaviours researchers watch for when an autonomous system starts acting
          against its operator’s intent. Two outcomes are deliberately <span className="text-ink">not</span>{" "}
          incidents: <span className="font-mono text-ink">harmless_malfunction</span> (a real glitch,
          but benign) and <span className="font-mono text-ink">insufficient_evidence</span> (the
          classifier abstains). Keeping “not enough evidence” separate from “no incident” is what
          stops the data from over- or under-counting.
        </p>
        <Card className="p-6">
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3">
            {Object.entries(INCIDENT_TYPES).map(([name, desc]) => (
              <li key={name} className="flex items-start gap-3">
                <span className="shrink-0 mt-0.5">
                  <TypeBadge type={name} />
                </span>
                <span className="text-sm text-muted">{desc}</span>
              </li>
            ))}
          </ul>
        </Card>
      </section>

      {/* Limitations */}
      <section>
        <SectionHeader eyebrow="Honest scope" title="Limitations you should know" />
        <div className="max-w-3xl space-y-3 text-muted leading-relaxed text-sm">
          <p>
            <span className="text-ink">This is a demo instance.</span> Classifications are automated
            and unverified until a human reviews them.
          </p>
          <p>
            <span className="text-ink">The default classifier is a keyword baseline</span>, chosen so
            the whole system runs with no model server or API key. It is transparent but simplistic;
            a local (Ollama) or hosted (Anthropic) model can be swapped in and measured with the same
            evaluation.
          </p>
          <p>
            <span className="text-ink">Coverage is a sample, not a census.</span> It reflects the
            configured sources and search terms, not all public reports everywhere.
          </p>
          <p>
            Evidence retention is <span className="text-ink">privacy-conscious</span> (author names
            hashed, raw payloads content-addressed) — not a claim of legal compliance.
          </p>
        </div>
      </section>
    </div>
  );
}

function Field({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div>
      <div
        className={`font-mono text-[0.62rem] uppercase tracking-[0.16em] ${
          accent ? "text-brand" : "text-faint"
        }`}
      >
        {label}
      </div>
      <p className="text-[0.82rem] text-muted mt-1.5 leading-relaxed">{value}</p>
    </div>
  );
}
