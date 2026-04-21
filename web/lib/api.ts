export type HttpMethod =
  | "GET"
  | "POST"
  | "PUT"
  | "PATCH"
  | "DELETE"
  | "HEAD"
  | "OPTIONS";

export interface TestRequest {
  url: string;
  method: HttpMethod;
  headers: Record<string, string>;
  body: string | null;
  concurrency: number;
  duration_seconds: number;
}

export interface LatencyStats {
  p50: number;
  p90: number;
  p95: number;
  p99: number;
  min: number;
  max: number;
  mean: number;
}

export interface BucketPoint {
  t: number;
  rps: number;
  count: number;
}

export interface StatusBreakdownItem {
  key: string;
  count: number;
  ratio: number;
}

export interface TestResponse {
  id: string;
  url: string;
  method: string;
  concurrency: number;
  duration_seconds: number;
  total_requests: number;
  total_errors: number;
  error_rate: number;
  latency_ms: LatencyStats;
  status_breakdown: StatusBreakdownItem[];
  rps_timeline: BucketPoint[];
  latency_heatmap: number[][];
  latency_buckets_ms: number[];
  health_report: string;
  mock: boolean;
}

export interface HealthResponse {
  ok: boolean;
  mock_mode: boolean;
}

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

export async function runTest(req: TestRequest): Promise<TestResponse> {
  const res = await fetch(`${BASE_URL}/test`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Test failed (${res.status}): ${detail}`);
  }
  return (await res.json()) as TestResponse;
}

export async function fetchHealth(): Promise<HealthResponse | null> {
  try {
    const res = await fetch(`${BASE_URL}/health`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as HealthResponse;
  } catch {
    return null;
  }
}
