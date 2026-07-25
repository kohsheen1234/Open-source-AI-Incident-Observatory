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

const AXIS = "#aeb9b9"; // readable label color on the dark card
const GRID = "#232b2b";
const SOURCE_COLORS = ["#18b2ba", "#ce2f00", "#5aa17f", "#4c8dc9"];
const TICK = { fill: "#aeb9b9", fontSize: 12 };

const tooltipStyle = {
  backgroundColor: "#131717",
  border: "1px solid #2b3333",
  borderRadius: 8,
  color: "#e9eceb",
  fontSize: 12,
};
// Recharts styles the tooltip title and item rows separately from the box.
const labelStyle = { color: "#e9eceb", fontWeight: 600 };
const itemStyle = { color: "#aeb9b9" };

export function TypeBar({ data }: { data: { type: string; count: number }[] }) {
  const sorted = [...data].sort((a, b) => a.count - b.count);
  return (
    <ResponsiveContainer width="100%" height={Math.max(220, sorted.length * 34)}>
      <BarChart data={sorted} layout="vertical" margin={{ left: 8, right: 16 }}>
        <CartesianGrid horizontal={false} stroke={GRID} />
        <XAxis type="number" stroke={AXIS} tick={TICK} />
        <YAxis type="category" dataKey="type" width={150} stroke={AXIS} tick={TICK} />
        <Tooltip contentStyle={tooltipStyle} labelStyle={labelStyle} itemStyle={itemStyle} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
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
        <Tooltip contentStyle={tooltipStyle} labelStyle={labelStyle} itemStyle={itemStyle} />
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
            <stop offset="0%" stopColor="#18b2ba" stopOpacity={0.4} />
            <stop offset="100%" stopColor="#18b2ba" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={GRID} />
        <XAxis dataKey="date" stroke={AXIS} tick={TICK} />
        <YAxis stroke={AXIS} tick={TICK} allowDecimals={false} />
        <Tooltip contentStyle={tooltipStyle} labelStyle={labelStyle} itemStyle={itemStyle} />
        <Area isAnimationActive={false} type="monotone" dataKey="count" stroke="#18b2ba" strokeWidth={2} fill="url(#g)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function SeverityBar({ data }: { data: { severity: number; count: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ left: 4, right: 16 }}>
        <CartesianGrid vertical={false} stroke={GRID} />
        <XAxis dataKey="severity" stroke={AXIS} tick={TICK} />
        <YAxis stroke={AXIS} tick={TICK} allowDecimals={false} />
        <Tooltip contentStyle={tooltipStyle} labelStyle={labelStyle} itemStyle={itemStyle} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
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
        <XAxis type="number" dataKey="confidence" name="confidence" domain={[0, 1]} stroke={AXIS} tick={TICK} />
        <YAxis type="number" dataKey="severity" name="severity" domain={[0, 5]} stroke={AXIS} tick={TICK} />
        <ZAxis range={[80, 80]} />
        <Tooltip contentStyle={tooltipStyle} labelStyle={labelStyle} itemStyle={itemStyle} cursor={{ strokeDasharray: "3 3" }} />
        <Scatter isAnimationActive={false} data={points}>
          {points.map((p, i) => (
            <Cell key={i} fill={typeColor(p.type)} />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
}
