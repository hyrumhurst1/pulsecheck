"""Pydantic request/response schemas for Pulsecheck."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


class TestRequest(BaseModel):
    url: str = Field(..., description="Target URL (http/https only)")
    method: HttpMethod = "GET"
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[str] = None
    # NOTE: No Pydantic upper bound so enforce_caps() can return a clean 400 with our own message.
    concurrency: int = Field(50, ge=1)
    duration_seconds: int = Field(30, ge=1)


class LatencyStats(BaseModel):
    p50: float
    p90: float
    p95: float
    p99: float
    min: float
    max: float
    mean: float


class BucketPoint(BaseModel):
    # Seconds offset from test start (bucket left edge)
    t: int
    rps: float
    count: int


class StatusBreakdownItem(BaseModel):
    key: str  # e.g. "200", "500", "error:timeout"
    count: int
    ratio: float


class TestResponse(BaseModel):
    id: str
    url: str
    method: str
    concurrency: int
    duration_seconds: int
    total_requests: int
    total_errors: int
    error_rate: float
    latency_ms: LatencyStats
    status_breakdown: List[StatusBreakdownItem]
    rps_timeline: List[BucketPoint]
    latency_heatmap: List[List[int]]  # rows = time buckets, cols = latency buckets
    latency_buckets_ms: List[float]  # right edges of latency buckets
    health_report: str
    mock: bool
