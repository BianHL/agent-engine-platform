"""Shared SSRF protection utilities."""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

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

    # If hostname is already an IP literal, check and return it directly
    try:
        ip = ipaddress.ip_address(hostname)
        if not _is_safe_ip(ip):
            return False, f"Blocked IP: {ip}", None
        return True, "", str(ip)
    except ValueError:
        pass

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
    except socket.gaierror:
        pass

    return True, "", resolved_ip


def _is_safe_ip(ip) -> bool:
    for network in BLOCKED_IP_RANGES:
        if ip in network:
            return False
    return True
