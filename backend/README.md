# Pulsecheck — Backend

FastAPI service that runs load tests and generates an AI health report.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

## Run

```bash
# Mock mode (no Anthropic key required):
set ANTHROPIC_API_KEY=mock   # Windows cmd
# $env:ANTHROPIC_API_KEY="mock"  # PowerShell
uvicorn app.main:app --reload --port 8000
```

## Safety

- URL scheme must be http/https.
- Host is DNS-resolved server-side; any IP in 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, 169.254.0.0/16, ::1, fc00::/7, fe80::/10 is rejected with 400.
- concurrency hard-capped at 100; duration hard-capped at 60s.
- Request headers and body are NEVER logged.
