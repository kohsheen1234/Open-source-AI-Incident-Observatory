import type { ReactNode } from "react";
import { sevColor, typeColor } from "./theme";

export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <div className="font-mono text-brand text-xs uppercase tracking-[0.14em] mb-3">{children}</div>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`bg-surface border border-border rounded-xl ${className}`}>{children}</div>
  );
}

export function StatCard({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <Card className="p-4">
      <div className="font-mono text-[0.7rem] uppercase tracking-wider text-muted">{label}</div>
      <div className="text-3xl font-bold text-ink mt-1">{value}</div>
      {hint && <div className="text-xs text-muted mt-1">{hint}</div>}
    </Card>
  );
}

export function Pill({ text, color }: { text: string; color: string }) {
  return (
    <span
      className="inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold text-white whitespace-nowrap"
      style={{ backgroundColor: color }}
    >
      {text}
    </span>
  );
}

export function TypeBadge({ type }: { type: string | null }) {
  return <Pill text={type ?? "unclassified"} color={typeColor(type)} />;
}

export function SeverityChip({ severity }: { severity: number | null }) {
  return (
    <Pill text={severity == null ? "severity —" : `severity ${severity}/5`} color={sevColor(severity)} />
  );
}

export function Spinner({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
      <div className="h-10 w-10 rounded-full border-2 border-border border-t-brand animate-spin" />
      <p className="text-muted max-w-md">{label}</p>
    </div>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return <h2 className="text-xl font-bold text-ink tracking-tight mb-3">{children}</h2>;
}
