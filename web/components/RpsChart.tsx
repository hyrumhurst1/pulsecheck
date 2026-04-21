"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { BucketPoint } from "@/lib/api";

export default function RpsChart({ data }: { data: BucketPoint[] }) {
  if (!data.length) {
    return <div className="text-gray-500 text-sm">No timeline data.</div>;
  }
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data}>
        <CartesianGrid stroke="#23262d" strokeDasharray="3 3" />
        <XAxis
          dataKey="t"
          stroke="#9ca3af"
          tickFormatter={(v) => `${v}s`}
          fontSize={12}
        />
        <YAxis stroke="#9ca3af" fontSize={12} />
        <Tooltip
          contentStyle={{ background: "#13151a", border: "1px solid #23262d" }}
          labelStyle={{ color: "#e6e8eb" }}
          formatter={(v: number) => [`${v.toFixed(1)}`, "rps"]}
          labelFormatter={(l) => `t=${l}s`}
        />
        <Bar dataKey="rps" fill="#f59e0b" />
      </BarChart>
    </ResponsiveContainer>
  );
}
