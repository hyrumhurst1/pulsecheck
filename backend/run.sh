#!/usr/bin/env bash
# Convenience launcher for Pulsecheck backend.
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
pip install -q -r requirements.txt
exec uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
