"""Unit tests for API Token management."""
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from jose import JWTError

from app.core.auth import _authenticate_token, get_current_user


# ---------------------------------------------------------------------------
# Token generation and hashing
# ---------------------------------------------------------------------------

class TestTokenGeneration:
    def test_token_urlsafe_generates_unique_values(self):
        """secrets.token_urlsafe should produce unique strings."""
        tokens = {secrets.token_urlsafe(32) for _ in range(100)}
        assert len(tokens) == 100

    def test_sha256_hash_consistency(self):
        """Same input should always produce the same SHA-256 hash."""
        raw = "test-token-value"
        h1 = hashlib.sha256(raw.encode()).hexdigest()
        h2 = hashlib.sha256(raw.encode()).hexdigest()
        assert h1 == h2

    def test_sha256_hash_differs_for_different_inputs(self):
        h1 = hashlib.sha256(b"token-a").hexdigest()
        h2 = hashlib.sha256(b"token-b").hexdigest()
        assert h1 != h2

    def test_hash_is_hex_string(self):
        h = hashlib.sha256(b"test").hexdigest()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_token_length(self):
        """token_urlsafe(32) should produce ~43 characters (base64url of 32 bytes)."""
        token = secrets.token_urlsafe(32)
        assert len(token) >= 40


# ---------------------------------------------------------------------------
# Token auth fallback from JWT
# ---------------------------------------------------------------------------

class TestTokenAuthFallback:
    @pytest.mark.asyncio
    async def test_jwt_auth_succeeds(self):
        """When a valid JWT is provided, it should be used directly."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "jwt-token"

        mock_db = AsyncMock()

        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.username = "testuser"
        mock_user.email = "test@test.com"
        mock_user.role = "admin"
        mock_user.tenant_id = "t1"
        mock_user.department_id = None
        mock_user.status = "active"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.core.auth.decode_token", return_value={"sub": "u1"}):
            result = await _authenticate_token(mock_credentials, mock_db)
            assert result["id"] == "u1"
            assert result["_auth_method"] == "jwt"

    @pytest.mark.asyncio
    async def test_api_token_fallback_when_jwt_fails(self):
        """When JWT decode fails, should fall back to API token lookup."""
        mock_credentials = MagicMock()
        raw_token = "my-api-token"
        mock_credentials.credentials = raw_token

        mock_db = AsyncMock()

        # API token mock
        mock_api_token = MagicMock()
        mock_api_token.user_id = "u1"
        mock_api_token.expires_at = datetime.now(UTC) + timedelta(days=10)
        mock_api_token.permissions = ["agent:read"]
        mock_api_token.status = "active"
        mock_api_token.last_used_at = None

        # User mock
        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.username = "testuser"
        mock_user.email = "test@test.com"
        mock_user.role = "admin"
        mock_user.tenant_id = "t1"
        mock_user.department_id = None
        mock_user.status = "active"

        # First call: JWT fails (raises)
        # Second call: API token lookup succeeds
        # Third call: User lookup succeeds
        mock_result_token = MagicMock()
        mock_result_token.scalar_one_or_none.return_value = mock_api_token
        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none.return_value = mock_user

        mock_db.execute = AsyncMock(side_effect=[mock_result_token, mock_result_user])
        mock_db.flush = AsyncMock()

        with patch("app.core.auth.decode_token", side_effect=JWTError("JWT decode failed")):
            result = await _authenticate_token(mock_credentials, mock_db)
            assert result["id"] == "u1"
            assert result["_auth_method"] == "api_token"
            assert result["_token_permissions"] == ["agent:read"]

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self):
        """Both JWT and API token failure should raise 401."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "bad-token"

        mock_db = AsyncMock()

        # API token lookup returns None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.core.auth.decode_token", side_effect=JWTError("bad")):
            with pytest.raises(HTTPException) as exc_info:
                await _authenticate_token(mock_credentials, mock_db)
            assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Token expiry check
# ---------------------------------------------------------------------------

class TestTokenExpiry:
    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self):
        """An API token past its expiry should be rejected."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "expired-api-token"

        mock_db = AsyncMock()

        mock_api_token = MagicMock()
        mock_api_token.user_id = "u1"
        mock_api_token.expires_at = datetime.now(UTC) - timedelta(hours=1)
        mock_api_token.permissions = []
        mock_api_token.status = "active"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_api_token
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.core.auth.decode_token", side_effect=JWTError("bad jwt")):
            with pytest.raises(HTTPException) as exc_info:
                await _authenticate_token(mock_credentials, mock_db)
            assert exc_info.value.status_code == 401
            assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_token_without_expiry_is_valid(self):
        """An API token with no expiry should be accepted."""
        mock_credentials = MagicMock()
        raw_token = "no-expiry-token"
        mock_credentials.credentials = raw_token

        mock_db = AsyncMock()

        mock_api_token = MagicMock()
        mock_api_token.user_id = "u1"
        mock_api_token.expires_at = None  # no expiry
        mock_api_token.permissions = []
        mock_api_token.status = "active"
        mock_api_token.last_used_at = None

        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.username = "testuser"
        mock_user.email = "test@test.com"
        mock_user.role = "admin"
        mock_user.tenant_id = "t1"
        mock_user.department_id = None
        mock_user.status = "active"

        mock_result_token = MagicMock()
        mock_result_token.scalar_one_or_none.return_value = mock_api_token
        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none.return_value = mock_user

        mock_db.execute = AsyncMock(side_effect=[mock_result_token, mock_result_user])
        mock_db.flush = AsyncMock()

        with patch("app.core.auth.decode_token", side_effect=JWTError("bad jwt")):
            result = await _authenticate_token(mock_credentials, mock_db)
            assert result["id"] == "u1"


# ---------------------------------------------------------------------------
# Token permissions scope
# ---------------------------------------------------------------------------

class TestTokenPermissions:
    @pytest.mark.asyncio
    async def test_token_permissions_passed_through(self):
        """Token's permissions scope should be included in user dict."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "scoped-token"

        mock_db = AsyncMock()

        mock_api_token = MagicMock()
        mock_api_token.user_id = "u1"
        mock_api_token.expires_at = None
        mock_api_token.permissions = ["agent:read", "agent:create"]
        mock_api_token.status = "active"
        mock_api_token.last_used_at = None

        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.username = "testuser"
        mock_user.email = "test@test.com"
        mock_user.role = "admin"
        mock_user.tenant_id = "t1"
        mock_user.department_id = None
        mock_user.status = "active"

        mock_result_token = MagicMock()
        mock_result_token.scalar_one_or_none.return_value = mock_api_token
        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none.return_value = mock_user

        mock_db.execute = AsyncMock(side_effect=[mock_result_token, mock_result_user])
        mock_db.flush = AsyncMock()

        with patch("app.core.auth.decode_token", side_effect=JWTError("bad jwt")):
            result = await _authenticate_token(mock_credentials, mock_db)
            assert result["_token_permissions"] == ["agent:read", "agent:create"]

    @pytest.mark.asyncio
    async def test_empty_token_permissions(self):
        """Token with empty permissions list should have empty scope."""
        mock_credentials = MagicMock()
        mock_credentials.credentials = "empty-scope-token"

        mock_db = AsyncMock()

        mock_api_token = MagicMock()
        mock_api_token.user_id = "u1"
        mock_api_token.expires_at = None
        mock_api_token.permissions = []
        mock_api_token.status = "active"
        mock_api_token.last_used_at = None

        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.username = "testuser"
        mock_user.email = "test@test.com"
        mock_user.role = "admin"
        mock_user.tenant_id = "t1"
        mock_user.department_id = None
        mock_user.status = "active"

        mock_result_token = MagicMock()
        mock_result_token.scalar_one_or_none.return_value = mock_api_token
        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none.return_value = mock_user

        mock_db.execute = AsyncMock(side_effect=[mock_result_token, mock_result_user])
        mock_db.flush = AsyncMock()

        with patch("app.core.auth.decode_token", side_effect=JWTError("bad jwt")):
            result = await _authenticate_token(mock_credentials, mock_db)
            assert result["_token_permissions"] == []
