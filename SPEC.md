# Pulsecheck — Build Spec

## Goal

Load-test any endpoint → latency heatmap, failure breakdown, AI-written health report.

## Stack (fixed for v1)

- Backend: Python 3.11+, FastAPI, `httpx[http2]`, asyncio, Pydantic, `anthropic`
- Frontend: Next.js 14 App Router, TypeScript, Tailwind, Recharts
- Two folders: `backend/` and `web/`

## MVP build order

1. `POST /test` accepts:
   ```json
   {
     "url": "https://...",
     "method": "GET|POST|...",
     "headers": {...},
     "body": "...",
     "concurrency": 50,
     "duration_seconds": 30
   }
   ```
2. asyncio worker: spawn N concurrent `httpx.AsyncClient` tasks, fire requests in a loop for `duration_seconds`, record `{timestamp, latency_ms, status_code, error_type}` per request.
3. Aggregation endpoint (or same response): p50/p90/p95/p99 latency, error rate by status_code, requests/sec timeline in 10s buckets.
4. Claude Haiku 4.5 call with aggregated stats. Prompt: "Diagnose this API run. Look for timeout clusters, 5xx spikes, cold-start curves, rate-limit walls. 3-sentence summary + 3 bullet findings."
5. Frontend: config form, Recharts heatmap (time buckets × latency buckets), status code pie, rendered health report.
6. Shareable result URL backed by in-memory cache (v1) or SQLite (v1.5). Supabase later.

## Hard safety rules (NON-NEGOTIABLE)

- Validate the URL: scheme in {http, https}, reject private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, 169.254.0.0/16, ::1, fc00::/7).
- Resolve DNS server-side and re-check the resolved IP against the private-range blocklist before firing.
- Cap concurrency at 100, duration at 60s.
- Log tester IP on every test.
- Never log request headers or body (may contain secrets).

## Model routing

- **Haiku 4.5** (`claude-haiku-4-5-20251001`) — report writing, no deep reasoning needed.

## Out of scope for v1

- Auth, user accounts.
- WebSocket / gRPC targets — HTTP(S) only.
- Distributed testing (single-process is fine).

## Gotchas

- Do NOT deploy publicly without rate limiting by IP (this is a DDoS tool otherwise).
- CORS: `allow_origins=["http://localhost:3000"]` for dev.
- Keep `ANTHROPIC_API_KEY` server-side only.
