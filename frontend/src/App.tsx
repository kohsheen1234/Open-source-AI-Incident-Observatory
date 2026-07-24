import { useEffect, useState } from "react";
import { api } from "./api";
import { Spinner } from "./ui";
import { Explorer } from "./views/Explorer";
import { Overview } from "./views/Overview";
import { Review } from "./views/Review";

const VIEWS = ["Overview", "Incident Explorer", "Review Queue"] as const;
type View = (typeof VIEWS)[number];

export default function App() {
  const [view, setView] = useState<View>("Overview");
  const [ready, setReady] = useState<boolean | null>(null);

  async function waitForApi() {
    setReady(null);
    for (let i = 0; i < 25; i++) {
      if (await api.health()) {
        setReady(true);
        return;
      }
      await new Promise((r) => setTimeout(r, 3000));
    }
    setReady(false);
  }

  useEffect(() => {
    waitForApi();
  }, []);

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 shrink-0 border-r border-border bg-[#171717] hidden md:flex flex-col p-6">
        <div className="flex items-center gap-2 text-lg font-bold text-white">🔭 AgentWatch</div>
        <div className="text-xs text-muted mt-1">Public AI-agent incident observatory</div>

        <nav className="mt-8 flex flex-col gap-1">
          {VIEWS.map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`text-left px-3 py-2 rounded-md text-sm transition-colors ${
                view === v ? "bg-brand/10 text-brand font-medium" : "text-muted hover:text-ink hover:bg-panel"
              }`}
            >
              {v}
            </button>
          ))}
        </nav>

        <div className="mt-auto pt-8 text-xs text-muted space-y-3">
          <div className="border border-border rounded-lg p-3 bg-surface">
            <div className="font-mono uppercase tracking-wider text-[0.65rem] text-brand mb-1">Data sources</div>
            Hacker News (live), Reddit (optional), and a bundled sample set. A demo instance —
            classifications are automated and unverified until reviewed.
          </div>
          <div className="flex gap-3">
            <a href="https://kohsheen1234.github.io/Open-source-AI-Incident-Observatory/">Docs</a>
            <a href="https://github.com/kohsheen1234/Open-source-AI-Incident-Observatory">Code</a>
          </div>
        </div>
      </aside>

      <main className="flex-1 min-w-0">
        {/* Mobile nav */}
        <div className="md:hidden flex gap-1 p-3 border-b border-border bg-[#171717] overflow-x-auto">
          {VIEWS.map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`px-3 py-1.5 rounded-md text-xs whitespace-nowrap ${
                view === v ? "bg-brand/10 text-brand" : "text-muted"
              }`}
            >
              {v}
            </button>
          ))}
        </div>

        <div className="max-w-6xl mx-auto px-6 py-10">
          {ready === null && (
            <Spinner label="Connecting to the API… the first load after idle can take up to ~60s while the free-tier backend wakes up. Thanks for your patience." />
          )}
          {ready === false && (
            <div className="text-center py-24">
              <p className="text-muted mb-4">
                The API is still waking up (free-tier cold start). It should be ready shortly.
              </p>
              <button
                onClick={waitForApi}
                className="bg-brand hover:bg-brand-hover text-[#0b0f0d] font-semibold px-4 py-2 rounded-md"
              >
                Retry
              </button>
            </div>
          )}
          {ready === true && view === "Overview" && <Overview />}
          {ready === true && view === "Incident Explorer" && <Explorer />}
          {ready === true && view === "Review Queue" && <Review />}
        </div>
      </main>
    </div>
  );
}
