"""Claude Haiku 4.5 health report, with mock fallback."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

MODEL_ID = "claude-haiku-4-5-20251001"

_PROMPT = (
    "Diagnose this API run. Find timeout clusters, 5xx spikes, cold-start curves, "
    "rate-limit walls. Reply with a 3-sentence summary followed by exactly 3 bullet "
    "findings (use '- ' for bullets). Be direct and specific; quote percentile numbers "
    "and status codes from the stats."
)


def _is_mock() -> bool:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return True
    lowered = key.lower()
    if lowered == "mock":
        return True
    if lowered.startswith("sk-ant-...") or lowered == "sk-ant-":
        return True
    return False


def _mock_report(stats: Dict[str, Any]) -> str:
    lat = stats.get("latency_ms", {})
    p50 = lat.get("p50", 0)
    p95 = lat.get("p95", 0)
    p99 = lat.get("p99", 0)
    err = stats.get("error_rate", 0)
    total = stats.get("total_requests", 0)
    breakdown = stats.get("status_breakdown", [])
    top = ", ".join(f"{b['key']}={b['count']}" for b in breakdown[:4]) or "none"
    summary = (
        f"The endpoint handled {total} requests with a p50 of {p50:.0f} ms and p95 of "
        f"{p95:.0f} ms. Error rate was {err * 100:.1f}% ({top}). Tail latency at p99 "
        f"({p99:.0f} ms) suggests occasional slow paths worth investigating."
    )
    bullets = [
        f"- p50/p95/p99 latency: {p50:.0f}/{p95:.0f}/{p99:.0f} ms",
        f"- Error rate {err * 100:.1f}% across {total} requests; top codes: {top}",
        "- Mock report (ANTHROPIC_API_KEY not set or set to 'mock')",
    ]
    return summary + "\n\n" + "\n".join(bullets)


def health_report(stats: Dict[str, Any]) -> str:
    """Return the AI health report, or a canned mock if no API key is configured."""
    if _is_mock():
        return _mock_report(stats)

    try:
        from anthropic import Anthropic  # lazy import so mock mode has no hard dep
    except Exception:  # noqa: BLE001
        return _mock_report(stats)

    client = Anthropic()  # reads ANTHROPIC_API_KEY from env
    trimmed = {
        "total_requests": stats.get("total_requests"),
        "total_errors": stats.get("total_errors"),
        "error_rate": stats.get("error_rate"),
        "latency_ms": stats.get("latency_ms"),
        "status_breakdown": stats.get("status_breakdown", [])[:10],
        "rps_timeline": stats.get("rps_timeline"),
    }
    user_msg = _PROMPT + "\n\nSTATS:\n" + json.dumps(trimmed, default=float)

    try:
        resp = client.messages.create(
            model=MODEL_ID,
            max_tokens=500,
            messages=[{"role": "user", "content": user_msg}],
        )
        # Concatenate text blocks.
        parts = []
        for block in resp.content or []:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        out = "\n".join(parts).strip()
        return out or _mock_report(stats)
    except Exception as e:  # noqa: BLE001
        return f"(Health report unavailable: {type(e).__name__}) \n\n" + _mock_report(stats)
