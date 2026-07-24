import type { IncidentDetail, Page, Review, Stats } from "./types";

// Configured at build time via VITE_API_URL; falls back to the public API.
const BASE = (
  import.meta.env.VITE_API_URL ?? "https://agentwatch-api-7mhz.onrender.com"
).replace(/\/$/, "");

async function getJSON<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(BASE + path);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== "") url.searchParams.set(k, String(v));
    }
  }
  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
  return (await resp.json()) as T;
}

export const api = {
  async health(): Promise<boolean> {
    try {
      const r = await fetch(BASE + "/health");
      if (!r.ok) return false;
      const j = await r.json();
      return j?.status === "ok";
    } catch {
      return false;
    }
  },

  stats: () => getJSON<Stats>("/stats"),

  incidents: (params?: Record<string, string | number | undefined>) =>
    getJSON<Page>("/incidents", params),

  incident: (id: number) => getJSON<IncidentDetail>(`/incidents/${id}`),

  async review(id: number, body: { reviewer: string; decision: string; notes: string | null }): Promise<Review> {
    const r = await fetch(BASE + `/incidents/${id}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return (await r.json()) as Review;
  },
};

export const API_BASE = BASE;
