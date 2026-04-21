"use client";

interface Props {
  grid: number[][]; // rows = time buckets, cols = latency buckets
  latencyEdgesMs: number[]; // right edges; grid has one extra "overflow" column
  timeBucketSeconds?: number;
}

function cellColor(value: number, max: number): string {
  if (max <= 0 || value <= 0) return "#13151a";
  const t = Math.min(1, value / max);
  // Dark teal -> bright amber gradient
  const r = Math.round(18 + t * (245 - 18));
  const g = Math.round(50 + t * (158 - 50));
  const b = Math.round(80 + t * (11 - 80));
  return `rgb(${r},${g},${b})`;
}

export default function LatencyHeatmap({
  grid,
  latencyEdgesMs,
  timeBucketSeconds = 10,
}: Props) {
  const maxVal = grid.reduce(
    (m, row) => row.reduce((mm, v) => (v > mm ? v : mm), m),
    0,
  );
  const nCols = latencyEdgesMs.length + 1; // +1 overflow
  const colLabels = [
    ...latencyEdgesMs.map((e) => `≤${e}ms`),
    `>${latencyEdgesMs[latencyEdgesMs.length - 1]}ms`,
  ];

  return (
    <div className="overflow-x-auto">
      <table className="border-separate [border-spacing:2px] text-xs">
        <thead>
          <tr>
            <th className="text-left text-gray-400 font-normal pr-2">t (s)</th>
            {colLabels.map((l) => (
              <th
                key={l}
                className="text-gray-400 font-normal px-1 whitespace-nowrap"
              >
                {l}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {grid.map((row, ri) => (
            <tr key={ri}>
              <td className="text-gray-400 pr-2 whitespace-nowrap">
                {ri * timeBucketSeconds}–
                {(ri + 1) * timeBucketSeconds}
              </td>
              {Array.from({ length: nCols }).map((_, ci) => {
                const v = row[ci] ?? 0;
                return (
                  <td
                    key={ci}
                    className="w-8 h-8 align-middle text-center"
                    style={{
                      background: cellColor(v, maxVal),
                      color: v > maxVal * 0.6 ? "#0b0c0f" : "#9ca3af",
                    }}
                    title={`${v} requests in this cell`}
                  >
                    {v > 0 ? v : ""}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
