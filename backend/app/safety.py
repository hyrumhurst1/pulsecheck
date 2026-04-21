"""URL + DNS safety validation. Non-negotiable safety rules live here."""
from __future__ import annotations

import ipaddress
import socket
from typing import List, Tuple
from urllib.parse import urlparse


# Private / reserved ranges that are never allowed as targets.
_BLOCKED_V4_NETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
]
_BLOCKED_V6_NETS = [
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


class SafetyError(ValueError):
    """Raised when a request target violates safety rules."""


def _is_blocked_ip(ip: ipaddress._BaseAddress) -> bool:
    if isinstance(ip, ipaddress.IPv4Address):
        for net in _BLOCKED_V4_NETS:
            if ip in net:
                return True
    elif isinstance(ip, ipaddress.IPv6Address):
        for net in _BLOCKED_V6_NETS:
            if ip in net:
                return True
    # Also guard link-local / multicast / unspecified generically.
    if ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
        return True
    return False


def _resolve_all(host: str) -> List[ipaddress._BaseAddress]:
    """Resolve a host to all A/AAAA records."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise SafetyError(f"DNS resolution failed for host '{host}': {e}") from e
    out: List[ipaddress._BaseAddress] = []
    seen = set()
    for info in infos:
        addr = info[4][0]
        if addr in seen:
            continue
        seen.add(addr)
        try:
            out.append(ipaddress.ip_address(addr))
        except ValueError:
            continue
    if not out:
        raise SafetyError(f"Host '{host}' did not resolve to any IP.")
    return out


def validate_target(url: str) -> Tuple[str, List[str]]:
    """Validate scheme + resolve host + block private ranges.

    Returns (normalized_url, [resolved_ip_strings]).
    Raises SafetyError on any violation.
    """
    if not url or not isinstance(url, str):
        raise SafetyError("url must be a non-empty string.")

    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise SafetyError("Only http and https URLs are allowed.")
    host = parsed.hostname
    if not host:
        raise SafetyError("URL has no host component.")

    # If the host is already a literal IP, check it directly.
    literal: ipaddress._BaseAddress | None = None
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        if _is_blocked_ip(literal):
            raise SafetyError(
                f"Target IP {literal} is in a private/reserved range and is not allowed."
            )
        return url, [str(literal)]

    resolved = _resolve_all(host)
    for ip in resolved:
        if _is_blocked_ip(ip):
            raise SafetyError(
                f"Host '{host}' resolves to private/reserved IP {ip} — blocked."
            )
    return url, [str(ip) for ip in resolved]


def enforce_caps(concurrency: int, duration_seconds: int) -> None:
    """Hard caps, never exceeded regardless of what the client asks for."""
    if concurrency < 1 or concurrency > 100:
        raise SafetyError("concurrency must be between 1 and 100 (inclusive).")
    if duration_seconds < 1 or duration_seconds > 60:
        raise SafetyError("duration_seconds must be between 1 and 60 (inclusive).")
