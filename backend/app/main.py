"""FastAPI entrypoint for Pulsecheck."""
from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # noqa: BLE001
    pass

from .aggregator import (
    DEFAULT_LATENCY_EDGES_MS,
    error_rate,
    latency_heatmap,
    latency_stats,
    rps_timeline,
    status_breakdown,
)
from .mock_run import synthetic_records
from .reporter import health_report
from .runner import run_load_test
from .safety import SafetyError, enforce_caps, validate_target
from .schemas import TestRequest, TestResponse

# Narrow, structured logging. We deliberately NEVER log headers or body.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
logger = logging.getLogger("pulsecheck")

app = FastAPI(title="Pulsecheck", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory result cache for shareable URLs (v1).
_RESULTS: Dict[str, Dict[str, Any]] = {}


def _is_mock_mode() -> bool:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return True
    lowered = key.lower()
    if lowered == "mock":
        return True
    # Placeholder value from .env.example — treat as mock so accidental copies don't 500.
    if lowered.startswith("sk-ant-...") or lowered == "sk-ant-":
        return True
    return False


def _assemble_response(
    *,
    req: TestRequest,
    records,
    mock: bool,
) -> TestResponse:
    total, errors, err_rate = error_rate(records)
    stats_dict: Dict[str, Any] = {
        "total_requests": total,
        "total_errors": errors,
        "error_rate": err_rate,
        "latency_ms": latency_stats(records),
        "status_breakdown": status_breakdown(records),
        "rps_timeline": rps_timeline(records, req.duration_seconds),
    }
    heatmap = latency_heatmap(records, req.duration_seconds)
    # Generate the AI (or mock) health report.
    report = health_report(stats_dict)

    resp = TestResponse(
        id=uuid.uuid4().hex[:12],
        url=req.url or "mock://synthetic",
        method=req.method,
        concurrency=req.concurrency,
        duration_seconds=req.duration_seconds,
        total_requests=total,
        total_errors=errors,
        error_rate=err_rate,
        latency_ms=stats_dict["latency_ms"],
        status_breakdown=stats_dict["status_breakdown"],
        rps_timeline=stats_dict["rps_timeline"],
        latency_heatmap=heatmap,
        latency_buckets_ms=list(DEFAULT_LATENCY_EDGES_MS),
        health_report=report,
        mock=mock,
    )
    _RESULTS[resp.id] = resp.model_dump()
    return resp


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"ok": True, "mock_mode": _is_mock_mode()}


@app.post("/test", response_model=TestResponse)
async def post_test(req: TestRequest, request: Request) -> TestResponse:
    client_ip = request.client.host if request.client else "unknown"
    mock = _is_mock_mode()

    # MOCK SHORT-CIRCUIT: empty url or "mock" -> fabricate a synthetic run so the UI fully demos.
    if mock and (not req.url or req.url.strip().lower() in ("", "mock")):
        # Still cap the shape of the request.
        try:
            enforce_caps(req.concurrency, req.duration_seconds)
        except SafetyError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        logger.info(
            "test ip=%s mode=mock-synthetic concurrency=%d duration=%d",
            client_ip, req.concurrency, req.duration_seconds,
        )
        records = synthetic_records(req.concurrency, req.duration_seconds)
        return _assemble_response(req=req, records=records, mock=True)

    # Real request path: enforce safety rules.
    try:
        enforce_caps(req.concurrency, req.duration_seconds)
        normalized_url, resolved_ips = validate_target(req.url)
    except SafetyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    # SPEC rule: log tester IP on every test. NEVER log headers/body.
    logger.info(
        "test ip=%s url=%s resolved=%s method=%s concurrency=%d duration=%d",
        client_ip,
        normalized_url,
        ",".join(resolved_ips),
        req.method,
        req.concurrency,
        req.duration_seconds,
    )

    run = await run_load_test(
        url=normalized_url,
        method=req.method,
        headers=req.headers,
        body=req.body,
        concurrency=req.concurrency,
        duration_seconds=req.duration_seconds,
    )
    return _assemble_response(req=req, records=run.records, mock=mock)


@app.get("/result/{result_id}", response_model=TestResponse)
async def get_result(result_id: str) -> TestResponse:
    data = _RESULTS.get(result_id)
    if not data:
        raise HTTPException(status_code=404, detail="result not found (in-memory cache)")
    return TestResponse(**data)
