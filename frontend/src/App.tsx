import { useEffect, useState } from "react";
import { api } from "./api";
import { GhostButton, PrimaryButton, Spinner } from "./ui";
import { Explorer } from "./views/Explorer";
import { Overview } from "./views/Overview";
import { Review } from "./views/Review";

const VIEWS = ["Overview", "Explorer", "Review"] as const;
type View = (typeof VIEWS)[number];

const DOCS_URL = "https://kohsheen1234.github.io/Open-source-AI-Incident-Observatory/";
const REPO_URL = "https://github.com/kohsheen1234/Open-source-AI-Incident-Observatory";
const API_DOCS = "https://agentwatch-api-7mhz.onrender.com/docs";

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
    <div className="relative min-h-screen flex flex-col">
      <div className="page-bg" />
      <div className="grain" />

      <header className="sticky top-0 z-30 border-b border-border bg-bg/70 backdrop-blur-xl">
        <div className="max-w-content mx-auto px-6 h-16 flex items-center justify-between">
          <button onClick={() => setView("Overview")} className="flex items-center gap-2.5 group">
            <span className="text-xl">🔭</span>
            <span className="font-bold text-ink tracking-tight">AgentWatch</span>
            <span className="hidden sm:inline eyebrow ml-1">Observatory</span>
          </button>

          <nav className="hidden md:flex items-center gap-1">
            {VIEWS.map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`px-3.5 py-1.5 rounded-lg text-sm transition-colors ${
                  view === v ? "text-ink bg-panel" : "text-muted hover:text-ink"
                }`}
              >
                {v}
              </button>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <a className="text-sm text-muted hover:text-ink no-underline hidden sm:inline" href={API_DOCS} target="_blank" rel="noreferrer">
              API
            </a>
            <a className="text-sm text-muted hover:text-ink no-underline hidden sm:inline" href={DOCS_URL} target="_blank" rel="noreferrer">
              Docs
            </a>
            <GhostButton href={REPO_URL}>GitHub ↗</GhostButton>
          </div>
        </div>
        {/* mobile nav */}
        <div className="md:hidden flex gap-1 px-4 pb-3 overflow-x-auto">
          {VIEWS.map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`px-3 py-1.5 rounded-lg text-xs whitespace-nowrap ${
                view === v ? "text-ink bg-panel" : "text-muted"
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </header>

      <main className="relative z-10 flex-1 w-full max-w-content mx-auto px-6 py-12">
        {ready === null && (
          <Spinner label="Connecting to the API… the first load after idle can take up to ~60s while the free-tier backend wakes up. Thanks for your patience." />
        )}
        {ready === false && (
          <div className="text-center py-28">
            <p className="text-muted mb-5 max-w-md mx-auto">
              The API is still waking up (free-tier cold start). It should be ready in a few
              seconds.
            </p>
            <PrimaryButton onClick={waitForApi}>Retry</PrimaryButton>
          </div>
        )}
        {ready === true && view === "Overview" && <Overview onExplore={() => setView("Explorer")} />}
        {ready === true && view === "Explorer" && <Explorer />}
        {ready === true && view === "Review" && <Review />}
      </main>

      <footer className="relative z-10 border-t border-border">
        <div className="max-w-content mx-auto px-6 py-8 flex flex-col sm:flex-row gap-3 items-center justify-between text-sm text-faint">
          <div>AgentWatch — open-source observatory for public AI-agent incidents.</div>
          <div className="flex gap-4">
            <a href={REPO_URL} target="_blank" rel="noreferrer">GitHub</a>
            <a href={DOCS_URL} target="_blank" rel="noreferrer">Docs</a>
            <a href={API_DOCS} target="_blank" rel="noreferrer">API</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
