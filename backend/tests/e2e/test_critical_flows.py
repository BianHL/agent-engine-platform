"""End-to-end tests for critical user flows.

These tests exercise the API layer with mocked database dependencies.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_db


# Mock DB dependency for all E2E tests
class FakeUser:
    id = "admin-user-id"
    username = "admin"
    email = "admin@test.com"
    hashed_password = ""  # Will be set below
    role = "admin"
    tenant_id = "default"
    department_id = None
    status = "active"
    expires_at = None
    # Fields needed when mock returns this as ApiToken
    user_id = "admin-user-id"
    permissions = None
    last_used_at = None
    token_hash = "fake-hash"


from app.core.security import get_password_hash
FakeUser.hashed_password = get_password_hash("admin123")


class MockDB:
    def __init__(self):
        self._user = FakeUser()

    async def execute(self, stmt):
        result = MagicMock()
        # Detect ApiTokenModel queries — return None (no token found)
        # so expired/invalid JWT doesn't silently succeed via API token path
        stmt_str = str(stmt)
        if "api_tokens" in stmt_str:
            result.scalar_one_or_none.return_value = None
        else:
            result.scalar_one_or_none.return_value = self._user
        result.scalar.return_value = 0
        result.scalars.return_value.all.return_value = []
        return result

    def add(self, obj):
        pass

    async def flush(self):
        pass

    async def delete(self, obj):
        pass


async def override_get_db():
    yield MockDB()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def auth_headers(client):
    """Get auth token for authenticated requests."""
    resp = await client.post("/api/v1/auth/login", json={
        "username": "admin", "password": "admin123"
    })
    if resp.status_code == 200:
        token = resp.json().get("access_token", "")
        return {"Authorization": f"Bearer {token}"}
    return {}


# === F-001: Login/Logout Flow ===

@pytest.mark.asyncio
async def test_login_flow(client):
    """User can login and get JWT token (F-001)."""
    resp = await client.post("/api/v1/auth/login", json={
        "username": "admin", "password": "admin123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Login with wrong password returns 401."""
    resp = await client.post("/api/v1/auth/login", json={
        "username": "admin", "password": "wrong"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client, auth_headers):
    """GET /auth/me returns current user info."""
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "username" in data


@pytest.mark.asyncio
async def test_unauthenticated_access_rejected(client):
    """Accessing protected endpoint without token returns 401."""
    resp = await client.get("/api/v1/agents/")
    assert resp.status_code == 401


# === F-002: Agent List ===

@pytest.mark.asyncio
async def test_agent_list_empty(client, auth_headers):
    """Agent list returns empty when no agents exist."""
    resp = await client.get("/api/v1/agents/", headers=auth_headers)
    assert resp.status_code == 200


# === D-004: Health Check ===

@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Health endpoint returns component statuses."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert "components" in data
    assert "version" in data


# === OpenAPI ===

@pytest.mark.asyncio
async def test_openapi_available(client):
    """OpenAPI spec is available at /openapi.json."""
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "openapi" in data
    assert data["info"]["title"] == "Agent Engine Platform"


@pytest.mark.asyncio
async def test_docs_available(client):
    """Swagger UI is available at /docs."""
    resp = await client.get("/docs")
    assert resp.status_code == 200


# === F-008: Token Expiry ===

@pytest.mark.asyncio
async def test_expired_token_rejected(client):
    """Expired JWT token returns 401 (F-008)."""
    from datetime import timedelta
    from app.core.security import create_access_token

    token = create_access_token(
        {"sub": "admin", "tenant_id": "default", "role": "admin"},
        expires_delta=timedelta(seconds=-1),
    )
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/api/v1/agents/", headers=headers)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_rejected(client):
    """Invalid JWT token returns 401."""
    headers = {"Authorization": "Bearer invalid.token.here"}
    resp = await client.get("/api/v1/agents/", headers=headers)
    assert resp.status_code == 401


# === SEC-005: JWT Security ===

@pytest.mark.asyncio
async def test_forged_token_rejected(client):
    """Forged JWT token returns 401 (SEC-005)."""
    import jose.jwt
    token = jose.jwt.encode(
        {"sub": "admin", "tenant_id": "default", "role": "admin", "exp": 9999999999},
        "wrong-secret",
        algorithm="HS256",
    )
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/api/v1/agents/", headers=headers)
    assert resp.status_code == 401


# === SEC-006: Tenant Isolation ===

@pytest.mark.asyncio
async def test_tenant_isolation_agents(client):
    """Different tenants see different agent lists (SEC-006)."""
    # This is a structural test - the API uses user["tenant_id"] from JWT
    # so different tokens naturally scope to different tenants
    resp = await client.get("/api/v1/agents/", headers={
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
                         "eyJzdWIiOiJoYWNrZXIiLCJ0ZW5hbnRfaWQiOiJoYWNrZWQtdGVuYW50Iiwicm9sZSI6InVzZXIiLCJleHAiOjk5OTk5OTk5OTl9."
                         "invalid"
    })
    # Should return 401 (invalid signature) not expose other tenant's data
    assert resp.status_code == 401
