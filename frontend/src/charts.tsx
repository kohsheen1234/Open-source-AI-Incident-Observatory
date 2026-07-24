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

const AXIS = "#8b8b8b";
const GRID = "#2e2e2e";
const SOURCE_COLORS = ["#3ecf8e", "#3f88c5", "#f3a712", "#8367c7"];

const tooltipStyle = {
  backgroundColor: "#202020",
  border: "1px solid #2e2e2e",
  borderRadius: 8,
  color: "#ededed",
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
            <stop offset="0%" stopColor="#3ecf8e" stopOpacity={0.4} />
            <stop offset="100%" stopColor="#3ecf8e" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={GRID} />
        <XAxis dataKey="date" stroke={AXIS} fontSize={12} />
        <YAxis stroke={AXIS} fontSize={12} allowDecimals={false} />
        <Tooltip contentStyle={tooltipStyle} />
        <Area isAnimationActive={false} type="monotone" dataKey="count" stroke="#3ecf8e" strokeWidth={2} fill="url(#g)" />
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
