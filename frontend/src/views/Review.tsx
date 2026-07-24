import { useEffect, useState } from "react";
import { api } from "../api";
import { cleanText } from "../theme";
import type { IncidentDetail, Page } from "../types";
import { Card, Pill, SectionHeader, SeverityChip, TypeBadge } from "../ui";

const DECISIONS = ["accept", "override", "false_positive"] as const;

export function Review() {
  const [page, setPage] = useState<Page | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [detail, setDetail] = useState<IncidentDetail | null>(null);
  const [reviewer, setReviewer] = useState("reviewer");
  const [decision, setDecision] = useState<(typeof DECISIONS)[number]>("accept");
  const [notes, setNotes] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.incidents({ limit: 200 }).then((p) => {
      setPage(p);
      if (p.items.length) setSelected(p.items[0].id);
    });
  }, []);

  useEffect(() => {
    if (selected != null) {
      setSaved(false);
      api.incident(selected).then(setDetail).catch(() => setDetail(null));
    }
  }, [selected]);

  async function submit() {
    if (selected == null) return;
    try {
      await api.review(selected, { reviewer, decision, notes: notes || null });
      setSaved(true);
      setError("");
    } catch (e) {
      setError(String(e));
    }
  }

  const cls = detail?.classification;

  return (
    <div>
      <SectionHeader eyebrow="Human-in-the-loop" title="Review Queue" />
      <p className="text-muted mb-5 max-w-3xl -mt-2">
        Human-in-the-loop review. The classifier's label is a machine <span className="text-ink">opinion</span>;
        here a person <span className="text-ink">accepts</span>, <span className="text-ink">overrides</span>, or flags
        it as a <span className="text-ink">false positive</span>. Both are kept, so the classifier's accuracy can be
        measured over time.
      </p>

      <label className="text-sm text-muted block mb-6">
        Incident to review
        <select
          value={selected ?? ""}
          onChange={(e) => setSelected(Number(e.target.value))}
          className="mt-1 w-full bg-panel border border-border rounded-md px-3 py-2 text-ink"
        >
          {(page?.items ?? []).map((i) => (
            <option key={i.id} value={i.id}>
              #{i.id} — {i.title.slice(0, 80)}
            </option>
          ))}
        </select>
      </label>

      {detail && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-5">
            <div className="font-mono text-xs uppercase tracking-wider text-muted mb-2">Evidence</div>
            <h3 className="text-ink font-semibold">{detail.title}</h3>
            <a className="text-sm inline-block mt-1" href={detail.url} target="_blank" rel="noreferrer">
              View original post ↗
            </a>
            <p className="text-sm text-muted leading-relaxed mt-3">{cleanText(detail.body)}</p>
          </Card>

          <div>
            <Card className="p-5">
              <div className="font-mono text-xs uppercase tracking-wider text-muted mb-3">
                Machine classification
              </div>
              <div className="flex flex-wrap gap-2">
                <TypeBadge type={cls?.incident_type ?? null} />
                <SeverityChip severity={cls?.severity ?? null} />
                <Pill text={`confidence ${cls ? Math.round(cls.confidence * 100) : 0}%`} color="#3f88c5" />
                <Pill text={`model ${cls?.model_name ?? "—"}`} color="#495057" />
                {cls?.abstained && <Pill text="abstained" color="#6c757d" />}
              </div>
              {cls?.reasoning_summary && (
                <div className="text-sm text-brand bg-brand/10 border border-brand/30 rounded-lg px-3 py-2 mt-3">
                  {cls.reasoning_summary}
                </div>
              )}
            </Card>

            <Card className="p-5 mt-6">
              <div className="font-mono text-xs uppercase tracking-wider text-muted mb-3">Your review</div>
              <label className="text-sm text-muted block mb-3">
                Reviewer
                <input
                  value={reviewer}
                  onChange={(e) => setReviewer(e.target.value)}
                  className="mt-1 w-full bg-panel border border-border rounded-md px-3 py-2 text-ink"
                />
              </label>
              <div className="flex gap-2 mb-3">
                {DECISIONS.map((d) => (
                  <button
                    key={d}
                    onClick={() => setDecision(d)}
                    className={`text-sm px-3 py-1.5 rounded-md border ${
                      decision === d ? "border-brand text-brand bg-brand/10" : "border-border text-muted"
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Notes (optional)"
                className="w-full bg-panel border border-border rounded-md px-3 py-2 text-ink h-20"
              />
              <button
                onClick={submit}
                className="mt-3 bg-brand hover:bg-[#ffbb4d] text-[#1c1206] font-semibold px-4 py-2 rounded-lg"
              >
                Submit review
              </button>
              {saved && <p className="text-brand text-sm mt-3">Review saved and attached to this incident.</p>}
              {error && <p className="text-[#e4572e] text-sm mt-3">Could not save: {error}</p>}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
