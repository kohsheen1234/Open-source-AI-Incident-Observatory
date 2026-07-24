import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { IncidentSummary } from "./types";
import { sevColor, typeColor } from "./theme";

const AXIS = "#8a8072";
const GRID = "#2b241c";
const SOURCE_COLORS = ["#f5a524", "#ff7a18", "#e4a94b", "#c77d3a"];

const tooltipStyle = {
  backgroundColor: "#1b1611",
  border: "1px solid #2b241c",
  borderRadius: 8,
  color: "#f6efe4",
  fontSize: 12,
};

export function TypeBar({ data }: { data: { type: string; count: number }[] }) {
  const sorted = [...data].sort((a, b) => a.count - b.count);
  return (
    <ResponsiveContainer width="100%" height={Math.max(220, sorted.length * 34)}>
      <BarChart data={sorted} layout="vertical" margin={{ left: 8, right: 16 }}>
        <CartesianGrid horizontal={false} stroke={GRID} />
        <XAxis type="number" stroke={AXIS} fontSize={12} />
        <YAxis type="category" dataKey="type" width={150} stroke={AXIS} fontSize={12} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
        <Bar isAnimationActive={false} dataKey="count" radius={[0, 4, 4, 0]}>
          {sorted.map((d) => (
            <Cell key={d.type} fill={typeColor(d.type)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function SourceDonut({ data }: { data: { source: string; count: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie isAnimationActive={false} data={data} dataKey="count" nameKey="source" innerRadius={70} outerRadius={110} paddingAngle={2}>
          {data.map((d, i) => (
            <Cell key={d.source} fill={SOURCE_COLORS[i % SOURCE_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip contentStyle={tooltipStyle} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function TimeArea({ data }: { data: { date: string; count: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ left: 4, right: 16 }}>
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f5a524" stopOpacity={0.4} />
            <stop offset="100%" stopColor="#f5a524" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={GRID} />
        <XAxis dataKey="date" stroke={AXIS} fontSize={12} />
        <YAxis stroke={AXIS} fontSize={12} allowDecimals={false} />
        <Tooltip contentStyle={tooltipStyle} />
        <Area isAnimationActive={false} type="monotone" dataKey="count" stroke="#f5a524" strokeWidth={2} fill="url(#g)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function SeverityBar({ data }: { data: { severity: number; count: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ left: 4, right: 16 }}>
        <CartesianGrid vertical={false} stroke={GRID} />
        <XAxis dataKey="severity" stroke={AXIS} fontSize={12} />
        <YAxis stroke={AXIS} fontSize={12} allowDecimals={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
        <Bar isAnimationActive={false} dataKey="count" radius={[4, 4, 0, 0]}>
          {data.map((d) => (
            <Cell key={d.severity} fill={sevColor(d.severity)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ConfidenceScatter({ items }: { items: IncidentSummary[] }) {
  const points = items
    .filter((i) => i.classification && i.classification.severity != null)
    .map((i) => ({
      confidence: i.classification!.confidence,
      severity: i.classification!.severity as number,
      type: i.classification!.incident_type,
      title: i.title,
    }));
  return (
    <ResponsiveContainer width="100%" height={320}>
      <ScatterChart margin={{ left: 4, right: 16, top: 8, bottom: 8 }}>
        <CartesianGrid stroke={GRID} />
        <XAxis type="number" dataKey="confidence" name="confidence" domain={[0, 1]} stroke={AXIS} fontSize={12} />
        <YAxis type="number" dataKey="severity" name="severity" domain={[0, 5]} stroke={AXIS} fontSize={12} />
        <ZAxis range={[80, 80]} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ strokeDasharray: "3 3" }} />
        <Scatter isAnimationActive={false} data={points}>
          {points.map((p, i) => (
            <Cell key={i} fill={typeColor(p.type)} />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
}
