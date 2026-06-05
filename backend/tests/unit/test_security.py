"""Unit tests for Security module"""
import socket

import pytest
from app.core.security import (
    get_password_hash, verify_password,
    create_access_token, decode_token,
    encrypt, decrypt
)


def test_password_hash_roundtrip():
    password = "SecureP@ssw0rd!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)


def test_password_hash_different_each_time():
    p1 = get_password_hash("test")
    p2 = get_password_hash("test")
    assert p1 != p2  # bcrypt uses random salt


def test_wrong_password():
    hashed = get_password_hash("correct")
    assert not verify_password("wrong", hashed)


def test_token_roundtrip():
    data = {"sub": "user123", "role": "admin", "tenant_id": "t1"}
    token = create_access_token(data)
    decoded = decode_token(token)
    assert decoded["sub"] == "user123"
    assert decoded["role"] == "admin"


def test_token_contains_expiry():
    token = create_access_token({"sub": "user1"})
    decoded = decode_token(token)
    assert "exp" in decoded


def test_encrypt_decrypt_roundtrip():
    plaintext = "my-secret-api-key"
    encrypted = encrypt(plaintext)
    assert encrypted != plaintext
    decrypted = decrypt(encrypted)
    assert decrypted == plaintext


def test_encrypt_different_ciphertext():
    e1 = encrypt("test")
    e2 = encrypt("test")
    # Fernet uses random IV, so ciphertext differs
    # But both should decrypt to same value
    assert decrypt(e1) == decrypt(e2)


def test_decrypt_wrong_key():
    encrypted = encrypt("test")
    # Should still work since we use the same key from env
    decrypted = decrypt(encrypted)
    assert decrypted == "test"


# ---------------------------------------------------------------------------
# SSRF protection tests
# ---------------------------------------------------------------------------

from unittest.mock import patch
from app.core.ssrf import is_safe_url_with_ip, is_safe_url


def test_ssrf_blocks_private_ip():
    """Private IPs should be blocked."""
    safe, reason, ip = is_safe_url_with_ip("http://127.0.0.1/admin")
    assert not safe
    assert "127.0.0.1" in reason


def test_ssrf_blocks_localhost_hostname():
    """localhost should be blocked."""
    safe, reason, _ = is_safe_url_with_ip("http://localhost/admin")
    assert not safe
    assert "localhost" in reason


def test_ssrf_blocks_metadata_endpoint():
    """Cloud metadata endpoint should be blocked."""
    safe, reason, _ = is_safe_url_with_ip("http://169.254.169.254/latest/meta-data/")
    assert not safe


def test_ssrf_blocks_invalid_scheme():
    """Non-http(s) schemes should be blocked."""
    safe, reason, _ = is_safe_url_with_ip("ftp://example.com/file")
    assert not safe
    assert "Unsupported scheme" in reason


def test_ssrf_allows_public_url():
    """Public URLs should be allowed."""
    safe, reason, ip = is_safe_url_with_ip("https://example.com/api")
    assert safe
    assert reason == ""


@patch("app.core.ssrf.socket.getaddrinfo", side_effect=socket.gaierror("DNS failure"))
def test_ssrf_blocks_dns_failure(mock_getaddrinfo):
    """DNS resolution failure should block the URL (fail-closed)."""
    safe, reason, ip = is_safe_url_with_ip("http://unknown-host-12345.example/test")
    assert not safe
    assert "DNS resolution failed" in reason
    assert ip is None


@patch("app.core.ssrf.socket.getaddrinfo")
def test_ssrf_blocks_private_resolved_ip(mock_getaddrinfo):
    """URLs resolving to private IPs should be blocked."""
    import socket
    # Mock DNS to return a private IP
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("192.168.1.1", 80))
    ]
    safe, reason, ip = is_safe_url_with_ip("http://evil.example.com/admin")
    assert not safe
    assert "192.168.1.1" in reason


def test_ssrf_deprecated_wrapper():
    """is_safe_url (deprecated wrapper) should still work."""
    safe, reason = is_safe_url("http://127.0.0.1/admin")
    assert not safe


@patch("app.core.ssrf.socket.getaddrinfo", return_value=[])
def test_ssrf_blocks_empty_dns_result(mock_getaddrinfo):
    """When DNS returns no addresses, the URL should be blocked (fail-closed)."""
    safe, reason, ip = is_safe_url_with_ip("http://no-addresses.example.com/test")
    assert not safe
    assert "No addresses resolved" in reason
    assert ip is None


def test_ssrf_blocks_internal_tld():
    """Internal TLDs (.internal, .local) should be blocked."""
    safe, reason, _ = is_safe_url_with_ip("http://metadata.google.internal/")
    assert not safe
    assert "Blocked internal TLD" in reason or "Blocked hostname" in reason

    safe, reason, _ = is_safe_url_with_ip("http://my-service.local/")
    assert not safe
    assert "Blocked internal TLD" in reason

    safe, reason, _ = is_safe_url_with_ip("http://test.internal/")
    assert not safe
    assert "Blocked internal TLD" in reason
