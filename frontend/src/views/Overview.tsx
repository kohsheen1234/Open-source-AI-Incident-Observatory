import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { ConfidenceScatter, SeverityBar, SourceDonut, TimeArea, TypeBar } from "../charts";
import { INCIDENT_TYPES } from "../theme";
import type { Page, Stats } from "../types";
import { Card, Eyebrow, SectionTitle, StatCard } from "../ui";

const PIPELINE = [
  ["📥", "Collect", "Public posts pulled from Hacker News (live search API), Reddit (optional), and a bundled sample set."],
  ["🔒", "Preserve", "Each post is stored verbatim with a SHA-256 hash, so evidence survives even if the original is deleted."],
  ["🧭", "Classify", "An LLM/baseline classifier labels the incident type, severity, and confidence — and abstains when unsure."],
  ["✅", "Review", "Machine labels are opinions; a human can accept, override, or reject them. Both are kept."],
];

const TABS = ["Over time", "Severity", "Confidence × severity"] as const;

export function Overview() {
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
      <div className="relative hero-glow">
        <Eyebrow>Live · AI-agent incident monitoring</Eyebrow>
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white leading-tight">
          AI Incident Observatory
        </h1>
        <p className="text-muted max-w-3xl mt-4 leading-relaxed">
          As AI systems increasingly <span className="text-ink font-medium">act on their own</span> —
          running tools, taking actions, operating autonomously — people post about what happens when
          they misbehave. <span className="text-ink font-medium">AgentWatch turns those scattered,
          disappearing reports into a durable, measurable evidence base</span>, so researchers and
          safety teams can track how often incidents happen, what kinds occur, and how the picture
          changes over time.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-10">
        {PIPELINE.map(([emoji, title, body]) => (
          <Card key={title} className="p-5">
            <div className="text-2xl">{emoji}</div>
            <div className="font-semibold text-ink mt-2">{title}</div>
            <div className="text-sm text-muted mt-1 leading-relaxed">{body}</div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mt-8">
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

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mt-10">
        <div className="lg:col-span-3">
          <SectionTitle>Incidents by type</SectionTitle>
          <Card className="p-4">
            {agg.type.length ? <TypeBar data={agg.type} /> : <Empty />}
          </Card>
        </div>
        <div className="lg:col-span-2">
          <SectionTitle>By source</SectionTitle>
          <Card className="p-4">{agg.source.length ? <SourceDonut data={agg.source} /> : <Empty />}</Card>
        </div>
      </div>

      <div className="mt-10">
        <div className="flex gap-2 mb-3">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`font-mono text-xs uppercase tracking-wider px-3 py-1.5 rounded-md border ${
                tab === t
                  ? "border-brand text-brand bg-brand/10"
                  : "border-border text-muted hover:text-ink"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        <Card className="p-4">
          {tab === "Over time" && (agg.time.length ? <TimeArea data={agg.time} /> : <Empty />)}
          {tab === "Severity" && (agg.severity.length ? <SeverityBar data={agg.severity} /> : <Empty />)}
          {tab === "Confidence × severity" &&
            (page?.items.length ? <ConfidenceScatter items={page.items} /> : <Empty />)}
        </Card>
      </div>

      <details className="mt-10 border border-border rounded-xl bg-surface p-4">
        <summary className="cursor-pointer font-semibold text-ink">What do the incident types mean?</summary>
        <ul className="mt-3 space-y-1.5 text-sm text-muted">
          {Object.entries(INCIDENT_TYPES).map(([name, desc]) => (
            <li key={name}>
              <span className="font-mono text-ink">{name}</span> — {desc}
            </li>
          ))}
        </ul>
      </details>

      <p className="text-xs text-muted mt-6">
        Data collected from Hacker News (live) + a bundled sample set, classified by the baseline
        classifier. Classifications are automated and unverified until reviewed.
      </p>
    </div>
  );
}

function Empty() {
  return <div className="text-muted text-sm py-10 text-center">No data yet.</div>;
}
