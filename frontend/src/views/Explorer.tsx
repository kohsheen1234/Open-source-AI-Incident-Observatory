import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { INCIDENT_TYPES, cleanText } from "../theme";
import type { IncidentDetail, Page } from "../types";
import { Card, SectionTitle, SeverityChip, TypeBadge } from "../ui";

export function Explorer() {
  const [page, setPage] = useState<Page | null>(null);
  const [type, setType] = useState<string>("");
  const [minConf, setMinConf] = useState<number>(0);
  const [search, setSearch] = useState<string>("");
  const [selected, setSelected] = useState<number | null>(null);
  const [detail, setDetail] = useState<IncidentDetail | null>(null);

  useEffect(() => {
    api.incidents({ limit: 500, incident_type: type || undefined }).then(setPage).catch(() => {});
  }, [type]);

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
      <SectionTitle>Incident Explorer</SectionTitle>
      <p className="text-muted mb-5">
        Browse and filter every collected incident. <span className="text-ink">Each row is a real
        public post.</span>
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
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
        Showing {rows.length} of {page?.total ?? 0} incidents.
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
                return (
                  <tr
                    key={it.id}
                    className="border-b border-border/60 hover:bg-panel/60 cursor-pointer"
                    onClick={() => setSelected(it.id)}
                  >
                    <td className="px-4 py-3">
                      <TypeBadge type={c?.incident_type ?? null} />
                    </td>
                    <td className="px-4 py-3">
                      <SeverityChip severity={c?.severity ?? null} />
                    </td>
                    <td className="px-4 py-3">
                      <ConfidenceBar value={c?.confidence ?? 0} />
                    </td>
                    <td className="px-4 py-3 text-muted">{it.source}</td>
                    <td className="px-4 py-3 text-ink max-w-md truncate">{it.title}</td>
                    <td className="px-4 py-3">
                      <a href={it.url} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}>
                        open ↗
                      </a>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {detail && selected != null && (
        <Card className="p-5 mt-6">
          <div className="flex items-start justify-between gap-4">
            <h3 className="text-lg font-semibold text-ink">{detail.title}</h3>
            <button className="text-muted hover:text-ink" onClick={() => setSelected(null)}>
              ✕
            </button>
          </div>
          <div className="flex flex-wrap gap-2 my-3">
            <TypeBadge type={detail.classification?.incident_type ?? null} />
            <SeverityChip severity={detail.classification?.severity ?? null} />
          </div>
          {detail.classification?.reasoning_summary && (
            <div className="text-sm text-brand bg-brand/10 border border-brand/30 rounded-lg px-3 py-2 mb-3">
              Classifier reasoning: {detail.classification.reasoning_summary}
            </div>
          )}
          <p className="text-sm text-muted leading-relaxed">{cleanText(detail.body)}</p>
          <a className="text-sm inline-block mt-3" href={detail.url} target="_blank" rel="noreferrer">
            View original post ↗
          </a>
        </Card>
      )}
    </div>
  );
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
