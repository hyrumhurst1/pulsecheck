# Pulsecheck

**API load-testing observatory.** Fire concurrent requests at any endpoint, get a latency heatmap, failure breakdown, and AI-written health report.

## Stack

- Python + FastAPI + asyncio + httpx (backend)
- Next.js + TypeScript + Recharts (frontend)
- Anthropic Claude Haiku 4.5 (health reports)

## Features

- Configurable concurrency + duration (capped for safety)
- p50 / p90 / p95 / p99 latency
- Status-code breakdown, timeline buckets, error-type classification
- AI-written health report: diagnoses timeout clusters, 5xx spikes, cold-start curves

## Quickstart

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env                              # set ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000

# frontend (new terminal)
cd web
pnpm install
pnpm dev
```

Open http://localhost:3000.

## Safety

This is a load-testing tool. **Hard caps for v1:** concurrency ≤ 100, duration ≤ 60s, HTTP(S) only, no private IP ranges. Do not point this at endpoints you do not own or have explicit permission to test.

## License

MIT
