import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { ConfidenceScatter, SeverityBar, SourceDonut, TimeArea, TypeBar } from "../charts";
import { INCIDENT_TYPES } from "../theme";
import type { Page, Stats } from "../types";
import { Card, GhostButton, PrimaryButton, SectionHeader, StatCard } from "../ui";

const DOCS_URL = "https://kohsheen1234.github.io/Open-source-AI-Incident-Observatory/";

const PIPELINE = [
  ["01", "Collect", "Public posts pulled from Hacker News (live search API), Reddit (optional), and a bundled sample set."],
  ["02", "Preserve", "Each post is stored verbatim with a SHA-256 hash, so evidence survives even if the original is deleted."],
  ["03", "Classify", "An LLM/baseline classifier labels the incident type, severity, and confidence — and abstains when unsure."],
  ["04", "Review", "Machine labels are opinions; a human can accept, override, or reject them. Both are kept."],
];

const TABS = ["Over time", "Severity", "Confidence × severity"] as const;

export function Overview({ onExplore }: { onExplore?: () => void }) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [page, setPage] = useState<Page | null>(null);
  const [tab, setTab] = useState<(typeof TABS)[number]>("Over time");

  useEffect(() => {
    api.stats().then(setStats).catch(() => {});
    api.incidents({ limit: 500 }).then(setPage).catch(() => {});
  }, []);

  const agg = useMemo(() => {
    const items = page?.items ?? [];
    const byType: Record<string, number> = {};
    const bySource: Record<string, number> = {};
    const byDate: Record<string, number> = {};
    const bySeverity: Record<number, number> = {};
    let sevSum = 0;
    let sevN = 0;
    for (const it of items) {
      bySource[it.source] = (bySource[it.source] ?? 0) + 1;
      const c = it.classification;
      if (c?.incident_type) byType[c.incident_type] = (byType[c.incident_type] ?? 0) + 1;
      if (c?.severity != null) {
        bySeverity[c.severity] = (bySeverity[c.severity] ?? 0) + 1;
        sevSum += c.severity;
        sevN += 1;
      }
      if (it.published_at) {
        const d = it.published_at.slice(0, 10);
        byDate[d] = (byDate[d] ?? 0) + 1;
      }
    }
    return {
      type: Object.entries(byType).map(([type, count]) => ({ type, count })),
      source: Object.entries(bySource).map(([source, count]) => ({ source, count })),
      time: Object.entries(byDate)
        .map(([date, count]) => ({ date, count }))
        .sort((a, b) => a.date.localeCompare(b.date)),
      severity: [1, 2, 3, 4, 5]
        .filter((s) => bySeverity[s])
        .map((s) => ({ severity: s, count: bySeverity[s] })),
      sources: Object.keys(bySource).length,
      avgSev: sevN ? (sevSum / sevN).toFixed(1) : "—",
    };
  }, [page]);

  return (
    <div>
      {/* Hero */}
      <section className="text-center max-w-3xl mx-auto pt-6 pb-4">
        <div className="eyebrow mb-4">Live · AI-agent incident monitoring</div>
        <h1 className="font-display uppercase text-5xl md:text-8xl leading-[0.9] tracking-tight">
          <span className="grad-text">The observatory for</span>
          <br />
          <span className="text-ink">AI-agent incidents</span>
        </h1>
        <p className="text-muted text-lg leading-relaxed mt-7 max-w-2xl mx-auto">
          As AI systems increasingly act on their own, people post when they{" "}
          <span className="font-serif italic text-ink">misbehave</span> — deleting files, ignoring
          instructions, acting without permission. AgentWatch turns those scattered, disappearing
          reports into a durable, <span className="font-serif italic text-ink">measurable</span>{" "}
          evidence base.
        </p>
        <div className="flex flex-wrap gap-3 justify-center mt-8">
          <PrimaryButton onClick={onExplore}>Explore incidents →</PrimaryButton>
          <GhostButton href={DOCS_URL}>Read the docs</GhostButton>
        </div>
      </section>

      {/* KPI strip */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mt-10">
        <StatCard label="Incidents" value={stats?.total_incidents ?? "…"} hint="collected" />
        <StatCard label="Classified" value={stats?.total_classified ?? "…"} hint="labelled" />
        <StatCard
          label="Abstention"
          value={stats ? `${Math.round(stats.abstention_rate * 100)}%` : "…"}
          hint="declined to guess"
        />
        <StatCard label="Sources" value={agg.sources || "…"} hint="data sources" />
        <StatCard label="Avg severity" value={agg.avgSev} hint="scale 1–5" />
      </div>

      {/* Pipeline — editorial, hairline-divided steps */}
      <div className="mt-24">
        <SectionHeader eyebrow="How it works" title="From scattered posts to measurable evidence" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 border-t border-border mt-4">
          {PIPELINE.map(([num, title, body], i) => (
            <div
              key={title}
              className={`py-7 lg:pr-7 border-b border-border lg:border-b-0 lg:border-r lg:last:border-r-0 ${
                i > 0 ? "lg:pl-7" : ""
              }`}
            >
              <div className="font-mono text-brand text-xs tracking-[0.25em]">{num}</div>
              <h3 className="font-display uppercase text-2xl text-ink mt-5 tracking-tight leading-none">
                {title}
              </h3>
              <p className="text-sm text-muted mt-3 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Charts */}
      <div className="mt-16">
        <SectionHeader eyebrow="Breakdown" title="What kinds of incidents, and from where" />
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <Card className="lg:col-span-3 p-5">
            <h3 className="font-semibold text-ink mb-3">Incidents by type</h3>
            {agg.type.length ? <TypeBar data={agg.type} /> : <Empty />}
          </Card>
          <Card className="lg:col-span-2 p-5">
            <h3 className="font-semibold text-ink mb-3">By source</h3>
            {agg.source.length ? <SourceDonut data={agg.source} /> : <Empty />}
          </Card>
        </div>

        <div className="flex gap-2 mt-6 mb-3">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`font-mono text-xs uppercase tracking-wider px-3 py-1.5 rounded-lg border transition-colors ${
                tab === t ? "border-brand text-brand bg-brand/10" : "border-border text-muted hover:text-ink"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        <Card className="p-5">
          {tab === "Over time" && (agg.time.length ? <TimeArea data={agg.time} /> : <Empty />)}
          {tab === "Severity" && (agg.severity.length ? <SeverityBar data={agg.severity} /> : <Empty />)}
          {tab === "Confidence × severity" &&
            (page?.items.length ? <ConfidenceScatter items={page.items} /> : <Empty />)}
        </Card>
      </div>

      <details className="mt-10 border border-border rounded-2xl bg-surface p-5">
        <summary className="cursor-pointer font-semibold text-ink">What do the incident types mean?</summary>
        <ul className="mt-3 space-y-1.5 text-sm text-muted">
          {Object.entries(INCIDENT_TYPES).map(([name, desc]) => (
            <li key={name}>
              <span className="font-mono text-ink">{name}</span> — {desc}
            </li>
          ))}
        </ul>
      </details>

      <p className="text-xs text-faint mt-6">
        Data collected from Hacker News (live) + a bundled sample set, classified by the baseline
        classifier. Classifications are automated and unverified until reviewed.
      </p>
    </div>
  );
}

function Empty() {
  return <div className="text-muted text-sm py-10 text-center">No data yet.</div>;
}
