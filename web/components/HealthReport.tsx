"use client";

export default function HealthReport({ text }: { text: string }) {
  if (!text) return null;
  // Split into paragraph vs bullets by blank line.
  const parts = text.split(/\n{2,}/);
  return (
    <div className="space-y-3 text-sm leading-relaxed text-gray-200">
      {parts.map((p, i) => {
        const lines = p.split("\n").map((l) => l.trim()).filter(Boolean);
        const allBullets =
          lines.length > 0 && lines.every((l) => l.startsWith("- "));
        if (allBullets) {
          return (
            <ul key={i} className="list-disc pl-5 space-y-1">
              {lines.map((l, j) => (
                <li key={j}>{l.replace(/^-\s+/, "")}</li>
              ))}
            </ul>
          );
        }
        return <p key={i}>{p}</p>;
      })}
    </div>
  );
}
