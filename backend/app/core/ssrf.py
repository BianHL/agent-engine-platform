"""Shared SSRF protection utilities."""
from __future__ import annotations

import ipaddress
import logging
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

BLOCKED_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("0.0.0.0/8"),
]

BLOCKED_HOSTNAMES = {
    "localhost", "127.0.0.1", "0.0.0.0",
    "metadata.google.internal", "169.254.169.254",
    "[::1]",
}


def is_safe_url(url: str) -> tuple[bool, str]:
    """Check if URL is safe from SSRF. Returns (safe, reason).

    .. deprecated:: Use :func:`is_safe_url_with_ip` instead, which also
       returns the pinned resolved IP to prevent TOCTOU DNS rebinding.
    """
    safe, _reason, _ip = is_safe_url_with_ip(url)
    return safe, _reason


def is_safe_url_with_ip(url: str) -> tuple[bool, str, str | None]:
    """Check if URL is safe from SSRF and return the pinned resolved IP.

    Returns ``(is_safe, reason, resolved_ip)``.  When *is_safe* is True the
    caller **must** connect to *resolved_ip* directly (setting the Host header
    to the original hostname) to prevent DNS-rebinding TOCTOU attacks (FW-C02).
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL", None

    if parsed.scheme not in ("http", "https"):
        return False, f"Unsupported scheme: {parsed.scheme}", None

    hostname = parsed.hostname
    if not hostname:
        return False, "No hostname in URL", None

    if hostname in BLOCKED_HOSTNAMES:
        return False, f"Blocked hostname: {hostname}", None

    # Block reserved/internal TLDs used by cloud providers and local networks
    _BLOCKED_TLDS = (".internal", ".local", ".localhost")
    if any(hostname.endswith(tld) for tld in _BLOCKED_TLDS):
        return False, f"Blocked internal TLD: {hostname}", None

    # If hostname is already an IP literal, check and return it directly
    try:
        ip = ipaddress.ip_address(hostname)
        if not _is_safe_ip(ip):
            return False, f"Blocked IP: {ip}", None
        return True, "", str(ip)
    except ValueError:
        pass  # Not an IP literal, proceed to DNS resolution

    # Resolve via DNS, check every address, and pin the first safe one
    resolved_ip: str | None = None
    try:
        addr_infos = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for _family, _, _, _, sockaddr in addr_infos[:5]:
            addr = ipaddress.ip_address(sockaddr[0])
            if not _is_safe_ip(addr):
                return False, f"Resolved to blocked IP: {addr}", None
            if resolved_ip is None:
                resolved_ip = str(addr)
    except socket.gaierror as e:
        logger.warning("DNS resolution failed for %s: %s", hostname, e)
        return False, f"DNS resolution failed for hostname: {hostname}", None

    if resolved_ip is None:
        return False, f"No addresses resolved for hostname: {hostname}", None

    return True, "", resolved_ip


def _is_safe_ip(ip) -> bool:
    for network in BLOCKED_IP_RANGES:
        if ip in network:
            return False
    return True


async def safe_request(
    method: str,
    url: str,
    *,
    timeout: float = 30.0,
    follow_redirects: bool = False,
    **kwargs,
):
    """Make an HTTP request with SSRF protection and DNS-rebinding prevention.

    Validates the URL via :func:`is_safe_url_with_ip`, then connects to the
    pinned resolved IP (with the Host header set to the original hostname) so
    that a second DNS resolution cannot return a different (internal) address.

    Returns the ``httpx.Response`` on success.  Raises ``ValueError`` if the
    URL fails the SSRF check.
    """
    import httpx

    safe, reason, resolved_ip = is_safe_url_with_ip(url)
    if not safe:
        raise ValueError(f"URL blocked: {reason}")

    parsed = urlparse(url)
    hostname = parsed.hostname
    port = parsed.port
    scheme = parsed.scheme

    # Build the target URL using the pinned IP
    if port:
        target = f"{scheme}://{resolved_ip}:{port}{parsed.path}"
    else:
        target = f"{scheme}://{resolved_ip}{parsed.path}"
    if parsed.query:
        target += f"?{parsed.query}"

    # Set Host header to original hostname for virtual hosting / TLS SNI
    headers = kwargs.pop("headers", {})
    headers["Host"] = hostname

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=follow_redirects) as client:
        return await client.request(method, target, headers=headers, **kwargs)
