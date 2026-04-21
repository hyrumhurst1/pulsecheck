"""Synthetic run generator for mock-mode demos (no real network traffic)."""
from __future__ import annotations

import math
import random
from typing import List

from .runner import RequestRecord


def synthetic_records(concurrency: int, duration_seconds: int, seed: int = 42) -> List[RequestRecord]:
    rng = random.Random(seed)
    records: List[RequestRecord] = []
    # Simulate ~concurrency requests per second with a cold-start bulge in the first 5s
    # and a small 5xx spike in the middle.
    approx_rps = max(5, min(concurrency * 4, 400))
    total = approx_rps * duration_seconds
    for _ in range(total):
        ts = rng.random() * duration_seconds
        # Cold-start bulge: first 5s have higher mean latency.
        cold_factor = 1.0 + max(0.0, (5.0 - ts) / 5.0) * 1.8
        base = rng.gammavariate(2.0, 40.0) * cold_factor  # skewed latency
        # Occasional long tail.
        if rng.random() < 0.03:
            base += rng.uniform(800, 3000)
        status: int | None = 200
        error_type: str | None = None
        r = rng.random()
        # Mid-run 5xx spike between ts in [duration/2 - 3, duration/2 + 3]
        spike = abs(ts - duration_seconds / 2) < 3
        if spike and r < 0.12:
            status = 503
        elif r < 0.01:
            status = 500
        elif r < 0.015:
            status = None
            error_type = "timeout"
            base = max(base, 10000 + rng.uniform(0, 2000))
        elif r < 0.02:
            status = 429  # rate-limit wall
        records.append(
            RequestRecord(
                ts=ts,
                latency_ms=round(base, 2),
                status_code=status,
                error_type=error_type,
            )
        )
    records.sort(key=lambda x: x.ts)
    return records
