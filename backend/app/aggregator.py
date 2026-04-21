"""Turn raw RequestRecords into percentiles, buckets, heatmap."""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple

from .runner import RequestRecord


def _percentile(sorted_values: List[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * pct
    lo = int(k)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = k - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


def latency_stats(records: List[RequestRecord]) -> Dict[str, float]:
    lat = sorted(r.latency_ms for r in records if r.status_code is not None)
    if not lat:
        # Fall back to all records (including errors) so UI isn't empty.
        lat = sorted(r.latency_ms for r in records)
    if not lat:
        return {"p50": 0, "p90": 0, "p95": 0, "p99": 0, "min": 0, "max": 0, "mean": 0}
    return {
        "p50": _percentile(lat, 0.50),
        "p90": _percentile(lat, 0.90),
        "p95": _percentile(lat, 0.95),
        "p99": _percentile(lat, 0.99),
        "min": lat[0],
        "max": lat[-1],
        "mean": sum(lat) / len(lat),
    }


def status_breakdown(records: List[RequestRecord]) -> List[Dict[str, float]]:
    counter: Counter[str] = Counter()
    for r in records:
        if r.status_code is not None:
            counter[str(r.status_code)] += 1
        else:
            counter[f"error:{r.error_type or 'unknown'}"] += 1
    total = sum(counter.values()) or 1
    items = [
        {"key": k, "count": v, "ratio": v / total}
        for k, v in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
    return items


def rps_timeline(records: List[RequestRecord], duration_seconds: int, bucket_s: int = 10) -> List[Dict[str, float]]:
    n_buckets = max(1, (duration_seconds + bucket_s - 1) // bucket_s)
    counts = [0] * n_buckets
    for r in records:
        idx = min(n_buckets - 1, max(0, int(r.ts // bucket_s)))
        counts[idx] += 1
    out = []
    for i, c in enumerate(counts):
        out.append({"t": i * bucket_s, "count": c, "rps": c / float(bucket_s)})
    return out


def error_rate(records: List[RequestRecord]) -> Tuple[int, int, float]:
    total = len(records)
    errors = sum(
        1
        for r in records
        if r.error_type is not None
        or (r.status_code is not None and r.status_code >= 500)
    )
    return total, errors, (errors / total if total else 0.0)


# Default latency bucket edges in milliseconds (right-inclusive).
DEFAULT_LATENCY_EDGES_MS: List[float] = [
    25, 50, 100, 200, 400, 800, 1500, 3000, 6000, 12000,
]


def latency_heatmap(
    records: List[RequestRecord],
    duration_seconds: int,
    time_bucket_s: int = 10,
    latency_edges_ms: List[float] = DEFAULT_LATENCY_EDGES_MS,
) -> List[List[int]]:
    n_time = max(1, (duration_seconds + time_bucket_s - 1) // time_bucket_s)
    n_lat = len(latency_edges_ms) + 1  # +1 for overflow bucket
    grid = [[0] * n_lat for _ in range(n_time)]
    for r in records:
        ti = min(n_time - 1, max(0, int(r.ts // time_bucket_s)))
        # Find first edge >= latency_ms; else overflow bin.
        li = n_lat - 1
        for i, edge in enumerate(latency_edges_ms):
            if r.latency_ms <= edge:
                li = i
                break
        grid[ti][li] += 1
    return grid
