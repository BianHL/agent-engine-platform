"""Unit tests for Tenant Service - Quota and Feature Flags."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.platform.tenant_service.tenant_service import (
    TenantService,
    QuotaExceededError,
    FeatureDisabledError,
)


def _make_mock_db(tenant=None, agent_count=0):
    """Create a mock DB session."""
    db = AsyncMock()

    # Mock tenant result
    tenant_result = MagicMock()
    tenant_result.scalar_one_or_none.return_value = tenant

    # Mock count result
    count_result = MagicMock()
    count_result.scalar.return_value = agent_count

    # First call returns tenant, second returns count
    db.execute = AsyncMock(side_effect=[tenant_result, count_result])
    return db


class FakeTenant:
    def __init__(self, id="t1", max_agents=10, features=None, status="active"):
        self.id = id
        self.max_agents = max_agents
        self.features = features or {}
        self.status = status
        self.name = "Test"
        self.code = "test"
        self.created_at = None


# === Quota Tests (T-003) ===

@pytest.mark.asyncio
async def test_check_agent_quota_within_limit():
    """Quota check passes when under limit."""
    tenant = FakeTenant(max_agents=10)
    db = _make_mock_db(tenant=tenant, agent_count=5)
    svc = TenantService(db)
    result = await svc.check_agent_quota("t1")
    assert result is True


@pytest.mark.asyncio
async def test_check_agent_quota_exceeded():
    """Quota check raises when at limit (T-003)."""
    tenant = FakeTenant(max_agents=10)
    db = _make_mock_db(tenant=tenant, agent_count=10)
    svc = TenantService(db)
    with pytest.raises(QuotaExceededError):
        await svc.check_agent_quota("t1")


@pytest.mark.asyncio
async def test_check_agent_quota_no_tenant():
    """Quota check passes when tenant not found."""
    db = _make_mock_db(tenant=None, agent_count=0)
    svc = TenantService(db)
    result = await svc.check_agent_quota("unknown")
    assert result is True


# === Feature Flag Tests (T-005) ===

@pytest.mark.asyncio
async def test_check_feature_enabled():
    """Feature check passes when feature is enabled."""
    tenant = FakeTenant(features={"knowledge_base": True, "workflow": True})
    db = _make_mock_db(tenant=tenant)
    svc = TenantService(db)
    result = await svc.check_feature_enabled("t1", "knowledge_base")
    assert result is True


@pytest.mark.asyncio
async def test_check_feature_disabled():
    """Feature check raises when feature is disabled (T-005)."""
    tenant = FakeTenant(features={"knowledge_base": False})
    db = _make_mock_db(tenant=tenant)
    svc = TenantService(db)
    with pytest.raises(FeatureDisabledError):
        await svc.check_feature_enabled("t1", "knowledge_base")


@pytest.mark.asyncio
async def test_check_feature_not_configured():
    """Feature check passes when feature is not in config (default enabled)."""
    tenant = FakeTenant(features={})
    db = _make_mock_db(tenant=tenant)
    svc = TenantService(db)
    result = await svc.check_feature_enabled("t1", "knowledge_base")
    assert result is True


@pytest.mark.asyncio
async def test_check_feature_no_tenant():
    """Feature check passes when tenant not found."""
    db = _make_mock_db(tenant=None)
    svc = TenantService(db)
    result = await svc.check_feature_enabled("unknown", "knowledge_base")
    assert result is True


@pytest.mark.asyncio
async def test_update_features():
    """Updating feature flags merges with existing."""
    tenant = FakeTenant(features={"knowledge_base": True})
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = tenant
    db.execute = AsyncMock(return_value=result)
    svc = TenantService(db)
    resp = await svc.update_features("t1", {"workflow": False})
    assert resp["features"]["knowledge_base"] is True
    assert resp["features"]["workflow"] is False
