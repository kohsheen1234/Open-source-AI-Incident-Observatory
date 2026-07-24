import type { ReactNode } from "react";
import { sevColor, typeColor } from "./theme";

export function Eyebrow({ children }: { children: ReactNode }) {
  return <div className="eyebrow mb-3">{children}</div>;
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`bg-surface border border-border rounded-2xl shadow-card transition-colors hover:border-border-strong ${className}`}
    >
      {children}
    </div>
  );
}

export function StatCard({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <Card className="p-5">
      <div className="font-mono text-[0.68rem] uppercase tracking-[0.12em] text-faint">{label}</div>
      <div className="font-display text-4xl text-ink mt-2 tabular-nums">{value}</div>
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
    <Pill
      text={severity == null ? "severity —" : `severity ${severity}/5`}
      color={sevColor(severity)}
    />
  );
}

export function PrimaryButton({
  children,
  onClick,
  href,
}: {
  children: ReactNode;
  onClick?: () => void;
  href?: string;
}) {
  const cls =
    "inline-flex items-center gap-1.5 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-[#1c1206] hover:bg-[#ffbb4d] transition-colors no-underline";
  return href ? (
    <a className={cls} href={href} target={href.startsWith("http") ? "_blank" : undefined} rel="noreferrer">
      {children}
    </a>
  ) : (
    <button className={cls} onClick={onClick}>
      {children}
    </button>
  );
}

export function GhostButton({ children, href }: { children: ReactNode; href: string }) {
  return (
    <a
      className="inline-flex items-center gap-1.5 rounded-lg border border-border-strong px-4 py-2 text-sm font-medium text-ink hover:border-brand hover:text-brand transition-colors no-underline"
      href={href}
      target={href.startsWith("http") ? "_blank" : undefined}
      rel="noreferrer"
    >
      {children}
    </a>
  );
}

export function Spinner({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-28 text-center">
      <div className="h-10 w-10 rounded-full border-2 border-border border-t-brand animate-spin" />
      <p className="text-muted max-w-md">{label}</p>
    </div>
  );
}

export function SectionHeader({ eyebrow, title }: { eyebrow?: string; title: string }) {
  return (
    <div className="mb-4">
      {eyebrow && <div className="eyebrow mb-2">{eyebrow}</div>}
      <h2 className="font-display uppercase text-3xl md:text-4xl text-ink tracking-tight leading-none">
        {title}
      </h2>
    </div>
  );
}
