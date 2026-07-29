import { Fragment, useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { INCIDENT_TYPES, cleanText } from "../theme";
import type { Classification, IncidentDetail, Page } from "../types";
import { Card, SectionHeader, SeverityChip, TypeBadge } from "../ui";

// What to show in the TYPE column. For a real incident, the incident type; otherwise the
// relevance verdict, so a confident "not an incident" never masquerades as an abstention.
function classLabel(c: Classification | null | undefined): string | null {
  if (!c) return null;
  if (c.relevance === "relevant") return c.incident_type;
  return c.relevance; // "not_relevant" | "insufficient_evidence"
}

// The report's own page (the HN thread) vs. the link it points to. For a Show HN the
// stored url is the submitted link (e.g. a GitHub repo); the discussion lives at the HN
// item. Prefer the discussion as "the post"; expose the submitted link separately.
function discussionUrl(it: { source: string; source_id: string | null }): string | null {
  if (it.source === "hackernews" && it.source_id) {
    return `https://news.ycombinator.com/item?id=${it.source_id}`;
  }
  return null;
}

export function Explorer() {
  const [page, setPage] = useState<Page | null>(null);
  const [type, setType] = useState<string>("");
  const [view, setView] = useState<"relevant" | "all">("relevant");
  const [minConf, setMinConf] = useState<number>(0);
  const [search, setSearch] = useState<string>("");
  const [selected, setSelected] = useState<number | null>(null);
  const [detail, setDetail] = useState<IncidentDetail | null>(null);

  useEffect(() => {
    api
      .incidents({
        limit: 500,
        incident_type: type || undefined,
        relevance: view === "relevant" ? "relevant" : undefined,
      })
      .then(setPage)
      .catch(() => {});
  }, [type, view]);

  useEffect(() => {
    if (selected != null) api.incident(selected).then(setDetail).catch(() => setDetail(null));
  }, [selected]);

  const rows = useMemo(() => {
    const items = page?.items ?? [];
    return items.filter((it) => {
      const c = it.classification;
      if (minConf > 0 && (c?.confidence ?? 0) < minConf) return false;
      if (search && !it.title.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [page, minConf, search]);

  return (
    <div>
      <SectionHeader eyebrow="Browse" title="Incident Explorer" />
      <p className="text-muted mb-5 -mt-2">
        {view === "relevant" ? (
          <>
            Confirmed AI-agent incidents — the classifier judged each one <span className="text-ink">a
            real incident</span>. Switch to “All collected posts” to see everything, including
            non-incidents.
          </>
        ) : (
          <>
            Every collected post, including ones the classifier ruled <span className="text-ink">not an
            incident</span>. Each row is a real public post.
          </>
        )}
      </p>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-5">
        <label className="text-sm text-muted">
          Show
          <select
            value={view}
            onChange={(e) => setView(e.target.value as "relevant" | "all")}
            className="mt-1 w-full bg-panel border border-border rounded-md px-3 py-2 text-ink"
          >
            <option value="relevant">Confirmed incidents</option>
            <option value="all">All collected posts</option>
          </select>
        </label>
        <label className="text-sm text-muted">
          Incident type
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="mt-1 w-full bg-panel border border-border rounded-md px-3 py-2 text-ink"
          >
            <option value="">All types</option>
            {Object.keys(INCIDENT_TYPES).map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm text-muted">
          Min confidence: <span className="text-brand font-mono">{minConf.toFixed(2)}</span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={minConf}
            onChange={(e) => setMinConf(Number(e.target.value))}
            className="mt-3 w-full accent-brand"
          />
        </label>
        <label className="text-sm text-muted">
          Search title
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="e.g. deleted, sandbox…"
            className="mt-1 w-full bg-panel border border-border rounded-md px-3 py-2 text-ink"
          />
        </label>
      </div>

      <p className="text-xs text-muted mb-2">
        Showing {rows.length} {view === "relevant" ? "confirmed incidents" : "collected posts"}
        {page?.total != null ? ` of ${page.total}` : ""}.
      </p>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left font-mono text-[0.7rem] uppercase tracking-wider text-muted border-b border-border">
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3 w-40">Confidence</th>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((it) => {
                const c = it.classification;
                const open = selected === it.id;
                return (
                  <Fragment key={it.id}>
                    <tr
                      className={`border-b border-border/60 hover:bg-panel/60 cursor-pointer ${
                        open ? "bg-panel/70" : ""
                      }`}
                      onClick={() => setSelected(open ? null : it.id)}
                    >
                      <td className="px-4 py-3">
                        <TypeBadge type={classLabel(c)} />
                      </td>
                      <td className="px-4 py-3">
                        <SeverityChip severity={c?.severity ?? null} />
                      </td>
                      <td className="px-4 py-3">
                        <ConfidenceBar value={c?.confidence ?? 0} />
                      </td>
                      <td className="px-4 py-3 text-muted">{it.source}</td>
                      <td className="px-4 py-3 text-ink max-w-md truncate">{it.title}</td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <a
                          href={discussionUrl(it) ?? it.url}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                        >
                          open ↗
                        </a>
                        <span className="ml-3 text-muted select-none">{open ? "▲" : "▼"}</span>
                      </td>
                    </tr>
                    {open && (
                      <tr className="border-b border-border/60 bg-panel/30">
                        <td colSpan={6} className="px-4 pb-5 pt-1">
                          {detail && detail.id === it.id ? (
                            <ExpandedDetail detail={detail} onClose={() => setSelected(null)} />
                          ) : (
                            <div className="text-muted text-sm py-3">Loading…</div>
                          )}
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

    </div>
  );
}

function ExpandedDetail({ detail, onClose }: { detail: IncidentDetail; onClose: () => void }) {
  const c = detail.classification;
  return (
    <div>
      <div className="flex items-start justify-between gap-4">
        <h3 className="text-base font-semibold text-ink">{detail.title}</h3>
        <button
          className="shrink-0 text-xs text-muted hover:text-ink border border-border rounded-md px-2 py-1"
          onClick={onClose}
        >
          Minimise ▲
        </button>
      </div>
      <div className="flex flex-wrap gap-2 mt-3">
        <TypeBadge type={classLabel(c)} />
        <SeverityChip severity={c?.severity ?? null} />
      </div>
      {c?.reasoning_summary && (
        <div className="text-sm text-brand bg-brand/10 border border-brand/30 rounded-lg px-3 py-2 my-3">
          Classifier reasoning: {c.reasoning_summary}
        </div>
      )}
      <p className="text-sm text-muted leading-relaxed whitespace-pre-wrap mt-3">
        {cleanText(detail.body)}
      </p>
      <div className="flex flex-wrap gap-x-5 gap-y-1 mt-3 text-sm">
        <a href={discussionUrl(detail) ?? detail.url} target="_blank" rel="noreferrer">
          View original post ↗
        </a>
        {discussionUrl(detail) && detail.url && detail.url !== discussionUrl(detail) && (
          <a className="text-muted" href={detail.url} target="_blank" rel="noreferrer">
            Linked resource: {shortHost(detail.url)} ↗
          </a>
        )}
      </div>
    </div>
  );
}

function shortHost(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "link";
  }
}

function ConfidenceBar({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-24 rounded-full bg-border overflow-hidden">
        <div className="h-full bg-brand" style={{ width: `${Math.round(value * 100)}%` }} />
      </div>
      <span className="font-mono text-xs text-muted">{value.toFixed(2)}</span>
    </div>
  );
}
