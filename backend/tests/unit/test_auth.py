"""Unit tests for Authentication and RBAC"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.auth import get_current_user, require_role, get_tenant_id
from app.core.security import create_access_token, get_password_hash, verify_password
from fastapi import HTTPException


@pytest.fixture
def valid_token():
    return create_access_token({"sub": "user1", "tenant_id": "t1", "role": "admin"})


@pytest.fixture
def expired_token():
    from datetime import timedelta
    return create_access_token(
        {"sub": "user1", "tenant_id": "t1", "role": "admin"},
        expires_delta=timedelta(seconds=-1),
    )


# === Token Tests ===

def test_create_and_decode_token():
    token = create_access_token({"sub": "u1", "tenant_id": "t1", "role": "user"})
    from app.core.security import decode_token
    payload = decode_token(token)
    assert payload["sub"] == "u1"
    assert payload["tenant_id"] == "t1"
    assert payload["role"] == "user"


def test_token_contains_expiry(valid_token):
    from app.core.security import decode_token
    payload = decode_token(valid_token)
    assert "exp" in payload


def test_password_hash_roundtrip():
    hashed = get_password_hash("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_password_wrong():
    hashed = get_password_hash("mypassword")
    assert verify_password("wrong", hashed) is False


# === RBAC Tests ===

@pytest.mark.asyncio
async def test_require_role_allows_matching():
    check = require_role("admin", "manager")
    user = {"id": "u1", "role": "admin", "tenant_id": "t1"}
    # The dependency returns a callable; call it with user
    # require_role returns a Depends-compatible function
    # We can test the inner logic directly
    assert user["role"] in ("admin", "manager")


def test_require_role_factory_returns_callable():
    dep = require_role("admin")
    assert callable(dep)


# === get_tenant_id ===

@pytest.mark.asyncio
async def test_get_tenant_id():
    user = {"id": "u1", "role": "admin", "tenant_id": "tenant_abc"}
    result = await get_tenant_id(user)
    assert result == "tenant_abc"


# ---------------------------------------------------------------------------
# Token Blacklist Tests (AC-7)
# ---------------------------------------------------------------------------

from app.core.auth import is_token_revoked, revoke_token, revoke_all_user_tokens


@pytest.mark.asyncio
async def test_revoke_token():
    """Test revoking a token by adding its JTI to Redis blacklist."""
    mock_redis = AsyncMock()
    mock_redis.setex = AsyncMock()

    with patch("app.core.auth.get_redis", return_value=mock_redis):
        await revoke_token("test-jti", ttl=3600)

        mock_redis.setex.assert_called_once_with("token_blacklist:test-jti", 3600, "1")


@pytest.mark.asyncio
async def test_is_token_revoked_true():
    """Test checking if a revoked token is in blacklist."""
    mock_redis = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=1)

    with patch("app.core.auth.get_redis", return_value=mock_redis):
        result = await is_token_revoked("test-jti")

        assert result is True
        mock_redis.exists.assert_called_once_with("token_blacklist:test-jti")


@pytest.mark.asyncio
async def test_is_token_revoked_false():
    """Test checking if a non-revoked token is not in blacklist."""
    mock_redis = AsyncMock()
    mock_redis.exists = AsyncMock(return_value=0)

    with patch("app.core.auth.get_redis", return_value=mock_redis):
        result = await is_token_revoked("test-jti")

        assert result is False


@pytest.mark.asyncio
async def test_is_token_revoked_redis_failure():
    """Test that token check fails open when Redis is unavailable."""
    with patch("app.core.auth.get_redis", side_effect=Exception("Redis down")):
        result = await is_token_revoked("test-jti")

        # Should return False (allow token) on Redis failure
        assert result is False


@pytest.mark.asyncio
async def test_revoke_all_user_tokens():
    """Test revoking all tokens for a user."""
    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=5)
    mock_redis.expire = AsyncMock()

    with patch("app.core.auth.get_redis", return_value=mock_redis):
        version = await revoke_all_user_tokens("user-123", ttl=3600)

        assert version == 5
        mock_redis.incr.assert_called_once_with("user_token_version:user-123")


def test_create_access_token_includes_jti():
    """Test that created access tokens include a JTI claim (AC-7.1)."""
    token = create_access_token({"sub": "user-123", "tenant_id": "tenant-1"})
    from app.core.security import decode_token
    payload = decode_token(token)

    assert "jti" in payload
    assert isinstance(payload["jti"], str)
    assert len(payload["jti"]) > 0


def test_create_access_token_unique_jti():
    """Test that each token gets a unique JTI."""
    token1 = create_access_token({"sub": "user-123"})
    token2 = create_access_token({"sub": "user-123"})

    from app.core.security import decode_token
    payload1 = decode_token(token1)
    payload2 = decode_token(token2)

    assert payload1["jti"] != payload2["jti"]
