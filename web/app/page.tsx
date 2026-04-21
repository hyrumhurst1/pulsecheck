"use client";

import { useEffect, useState } from "react";
import HealthReport from "@/components/HealthReport";
import LatencyHeatmap from "@/components/LatencyHeatmap";
import RpsChart from "@/components/RpsChart";
import StatusPie from "@/components/StatusPie";
import {
  fetchHealth,
  runTest,
  type HttpMethod,
  type TestRequest,
  type TestResponse,
} from "@/lib/api";

const METHODS: HttpMethod[] = [
  "GET",
  "POST",
  "PUT",
  "PATCH",
  "DELETE",
  "HEAD",
  "OPTIONS",
];

export default function Home() {
  const [url, setUrl] = useState("");
  const [method, setMethod] = useState<HttpMethod>("GET");
  const [headersText, setHeadersText] = useState("");
  const [body, setBody] = useState("");
  const [concurrency, setConcurrency] = useState(25);
  const [duration, setDuration] = useState(10);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TestResponse | null>(null);
  const [mockMode, setMockMode] = useState<boolean>(false);

  useEffect(() => {
    let alive = true;
    fetchHealth().then((h) => {
      if (alive && h) setMockMode(h.mock_mode);
    });
    return () => {
      alive = false;
    };
  }, []);

  function parseHeaders(raw: string): Record<string, string> {
    const out: Record<string, string> = {};
    raw
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean)
      .forEach((line) => {
        const idx = line.indexOf(":");
        if (idx > 0) {
          const k = line.slice(0, idx).trim();
          const v = line.slice(idx + 1).trim();
          if (k) out[k] = v;
        }
      });
    return out;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      const req: TestRequest = {
        url: url.trim(),
        method,
        headers: parseHeaders(headersText),
        body: body.length ? body : null,
        concurrency: Math.max(1, Math.min(100, Number(concurrency) || 1)),
        duration_seconds: Math.max(1, Math.min(60, Number(duration) || 1)),
      };
      const r = await runTest(req);
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">
          Pulsecheck
        </h1>
        <p className="text-gray-400 mt-1">
          Fire a burst at any HTTP endpoint. Get latency, failures, and an
          AI-written health report.
        </p>
      </header>

      {mockMode && (
        <div className="mb-6 rounded border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-300">
          <strong className="font-semibold">Mock mode.</strong>{" "}
          <code>ANTHROPIC_API_KEY</code> is not set — the health report is
          canned. Leave the URL empty or type <code>mock</code> to demo with a
          fully synthetic run (no outbound traffic).
        </div>
      )}

      <form
        onSubmit={onSubmit}
        className="grid gap-4 rounded-lg border border-edge bg-panel p-5"
      >
        <div className="grid grid-cols-[auto_1fr] gap-3">
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value as HttpMethod)}
            className="bg-ink border border-edge rounded px-3 py-2 text-sm"
          >
            {METHODS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
          <input
            type="text"
            placeholder={
              mockMode
                ? "https://api.example.com/ping   (or leave blank for mock)"
                : "https://api.example.com/ping"
            }
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="bg-ink border border-edge rounded px-3 py-2 text-sm font-mono"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <label className="text-xs text-gray-400">
            Concurrency (1–100)
            <input
              type="number"
              min={1}
              max={100}
              value={concurrency}
              onChange={(e) => setConcurrency(Number(e.target.value))}
              className="mt-1 w-full bg-ink border border-edge rounded px-3 py-2 text-sm text-gray-100"
            />
          </label>
          <label className="text-xs text-gray-400">
            Duration seconds (1–60)
            <input
              type="number"
              min={1}
              max={60}
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="mt-1 w-full bg-ink border border-edge rounded px-3 py-2 text-sm text-gray-100"
            />
          </label>
        </div>

        <label className="text-xs text-gray-400">
          Headers (one per line, <code>Name: Value</code>)
          <textarea
            rows={3}
            value={headersText}
            onChange={(e) => setHeadersText(e.target.value)}
            placeholder="User-Agent: pulsecheck/0.1"
            className="mt-1 w-full bg-ink border border-edge rounded px-3 py-2 text-sm font-mono text-gray-100"
          />
        </label>

        <label className="text-xs text-gray-400">
          Body (optional; raw string)
          <textarea
            rows={3}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder='{"ping": true}'
            className="mt-1 w-full bg-ink border border-edge rounded px-3 py-2 text-sm font-mono text-gray-100"
          />
        </label>

        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={running}
            className="rounded bg-amber-500 text-ink px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {running ? "Running…" : "Run test"}
          </button>
          {error && (
            <span className="text-rose-400 text-sm">{error}</span>
          )}
        </div>
      </form>

      {result && <Results r={result} />}
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-edge bg-panel px-3 py-2">
      <div className="text-[11px] uppercase tracking-wide text-gray-500">
        {label}
      </div>
      <div className="text-lg font-medium">{value}</div>
    </div>
  );
}

function Results({ r }: { r: TestResponse }) {
  const l = r.latency_ms;
  return (
    <section className="mt-8 space-y-6">
      <div className="flex items-baseline justify-between">
        <h2 className="text-xl font-semibold">Results</h2>
        <span className="text-xs text-gray-500 font-mono">id: {r.id}</span>
      </div>

      {r.mock && (
        <div className="rounded border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-xs text-amber-300">
          This run was served in <strong>mock mode</strong>.
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat label="Requests" value={r.total_requests.toLocaleString()} />
        <Stat
          label="Error rate"
          value={`${(r.error_rate * 100).toFixed(2)}%`}
        />
        <Stat label="p50 / p95" value={`${l.p50.toFixed(0)} / ${l.p95.toFixed(0)} ms`} />
        <Stat label="p99 / max" value={`${l.p99.toFixed(0)} / ${l.max.toFixed(0)} ms`} />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="rounded border border-edge bg-panel p-4">
          <h3 className="text-sm font-medium mb-3 text-gray-300">
            Requests per second (10s buckets)
          </h3>
          <RpsChart data={r.rps_timeline} />
        </div>
        <div className="rounded border border-edge bg-panel p-4">
          <h3 className="text-sm font-medium mb-3 text-gray-300">
            Status codes
          </h3>
          <StatusPie data={r.status_breakdown} />
        </div>
      </div>

      <div className="rounded border border-edge bg-panel p-4">
        <h3 className="text-sm font-medium mb-3 text-gray-300">
          Latency heatmap (time × latency)
        </h3>
        <LatencyHeatmap
          grid={r.latency_heatmap}
          latencyEdgesMs={r.latency_buckets_ms}
        />
      </div>

      <div className="rounded border border-edge bg-panel p-5">
        <h3 className="text-sm font-medium mb-3 text-gray-300">
          Health report
        </h3>
        <HealthReport text={r.health_report} />
      </div>
    </section>
  );
}
