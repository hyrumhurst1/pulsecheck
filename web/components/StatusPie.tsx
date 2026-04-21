"use client";

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { StatusBreakdownItem } from "@/lib/api";

const COLORS = [
  "#22c55e", // 2xx-ish
  "#eab308",
  "#f97316",
  "#ef4444",
  "#a855f7",
  "#06b6d4",
  "#84cc16",
  "#ec4899",
  "#3b82f6",
  "#f59e0b",
];

function colorForKey(key: string, idx: number): string {
  if (key.startsWith("2")) return "#22c55e";
  if (key.startsWith("3")) return "#06b6d4";
  if (key.startsWith("4")) return "#eab308";
  if (key.startsWith("5")) return "#ef4444";
  if (key.startsWith("error:")) return "#f43f5e";
  return COLORS[idx % COLORS.length];
}

export default function StatusPie({ data }: { data: StatusBreakdownItem[] }) {
  if (!data.length) {
    return <div className="text-gray-500 text-sm">No responses recorded.</div>;
  }
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="key"
          cx="50%"
          cy="50%"
          outerRadius={90}
          innerRadius={50}
          stroke="#0b0c0f"
        >
          {data.map((d, i) => (
            <Cell key={d.key} fill={colorForKey(d.key, i)} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: "#13151a", border: "1px solid #23262d" }}
          labelStyle={{ color: "#e6e8eb" }}
          formatter={(v: number, n: string) => [`${v}`, n]}
        />
        <Legend wrapperStyle={{ color: "#9ca3af", fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
