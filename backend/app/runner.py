"""Async load-test worker. Spawns N concurrent httpx tasks for a fixed duration."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import httpx


@dataclass
class RequestRecord:
    ts: float  # seconds offset from start
    latency_ms: float
    status_code: Optional[int]  # None if error
    error_type: Optional[str]  # e.g. "timeout", "connect", "read", or None


@dataclass
class RunOutput:
    records: List[RequestRecord] = field(default_factory=list)
    started_at: float = 0.0
    ended_at: float = 0.0


def _classify_error(exc: BaseException) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if isinstance(exc, httpx.ConnectError):
        return "connect"
    if isinstance(exc, httpx.ReadError):
        return "read"
    if isinstance(exc, httpx.RemoteProtocolError):
        return "protocol"
    if isinstance(exc, httpx.TooManyRedirects):
        return "redirects"
    if isinstance(exc, httpx.HTTPError):
        return "http"
    return type(exc).__name__.lower()


async def _worker(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    headers: Dict[str, str],
    body: Optional[str],
    stop_at: float,
    start_time: float,
    records: List[RequestRecord],
) -> None:
    while True:
        now = time.perf_counter()
        if now >= stop_at:
            return
        req_start = time.perf_counter()
        try:
            resp = await client.request(
                method=method,
                url=url,
                headers=headers or None,
                content=body.encode("utf-8") if body is not None else None,
            )
            latency_ms = (time.perf_counter() - req_start) * 1000.0
            records.append(
                RequestRecord(
                    ts=req_start - start_time,
                    latency_ms=latency_ms,
                    status_code=resp.status_code,
                    error_type=None,
                )
            )
            # Drain body to free the connection.
            await resp.aclose()
        except BaseException as exc:  # noqa: BLE001
            latency_ms = (time.perf_counter() - req_start) * 1000.0
            records.append(
                RequestRecord(
                    ts=req_start - start_time,
                    latency_ms=latency_ms,
                    status_code=None,
                    error_type=_classify_error(exc),
                )
            )


async def run_load_test(
    *,
    url: str,
    method: str,
    headers: Dict[str, str],
    body: Optional[str],
    concurrency: int,
    duration_seconds: int,
) -> RunOutput:
    """Fire `concurrency` workers in parallel for `duration_seconds`."""
    records: List[RequestRecord] = []
    timeout = httpx.Timeout(
        connect=10.0,
        read=max(10.0, float(duration_seconds)),
        write=10.0,
        pool=5.0,
    )
    limits = httpx.Limits(
        max_connections=concurrency * 2,
        max_keepalive_connections=concurrency,
    )
    start_time = time.perf_counter()
    stop_at = start_time + float(duration_seconds)

    async with httpx.AsyncClient(
        http2=True, timeout=timeout, limits=limits, follow_redirects=False
    ) as client:
        tasks = [
            asyncio.create_task(
                _worker(
                    client=client,
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    body=body,
                    stop_at=stop_at,
                    start_time=start_time,
                    records=records,
                )
            )
            for _ in range(concurrency)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    return RunOutput(records=records, started_at=start_time, ended_at=time.perf_counter())
