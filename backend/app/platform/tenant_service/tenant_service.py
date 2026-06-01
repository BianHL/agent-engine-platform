"""Tenant management service with quota and feature flag support."""
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AgentEngineError
from app.models.base import AgentModel, TenantModel


class QuotaExceededError(AgentEngineError):
    """Tenant has exceeded their quota."""
    pass


class FeatureDisabledError(AgentEngineError):
    """Feature is not enabled for this tenant."""
    pass


class TenantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> dict:
        """Create a new tenant and seed default RBAC roles."""
        tenant = TenantModel(
            name=data["name"],
            code=data["code"],
            max_agents=data.get("max_agents", 10),
            features=data.get("features", {}),
        )
        self.db.add(tenant)
        await self.db.flush()

        # Seed default RBAC roles for the new tenant
        from app.core.rbac import init_default_roles
        await init_default_roles(self.db, tenant.id)

        return {"id": tenant.id, "name": tenant.name, "code": tenant.code}

    async def get(self, tenant_id: str) -> Optional[dict]:
        """Get tenant by ID."""
        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        result = await self.db.execute(stmt)
        tenant = result.scalar_one_or_none()
        if not tenant:
            return None
        return {
            "id": tenant.id,
            "name": tenant.name,
            "code": tenant.code,
            "status": tenant.status,
            "max_agents": tenant.max_agents,
            "features": tenant.features or {},
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
        }

    async def check_agent_quota(self, tenant_id: str) -> bool:
        """Check if tenant can create more agents. Raises QuotaExceededError if not."""
        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        result = await self.db.execute(stmt)
        tenant = result.scalar_one_or_none()
        if not tenant:
            return True

        # Count existing agents
        count_stmt = select(func.count(AgentModel.id)).where(
            AgentModel.tenant_id == tenant_id
        )
        count_result = await self.db.execute(count_stmt)
        current_count = count_result.scalar() or 0

        if current_count >= tenant.max_agents:
            raise QuotaExceededError(
                f"Agent quota exceeded: {current_count}/{tenant.max_agents}"
            )
        return True

    async def check_feature_enabled(self, tenant_id: str, feature: str) -> bool:
        """Check if a feature is enabled for the tenant. Raises FeatureDisabledError if not."""
        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        result = await self.db.execute(stmt)
        tenant = result.scalar_one_or_none()
        if not tenant:
            return True

        features = tenant.features or {}
        if feature in features and features[feature] is False:
            raise FeatureDisabledError(f"Feature '{feature}' is disabled for this tenant")
        return True

    async def update_features(self, tenant_id: str, features: dict) -> dict:
        """Update tenant feature flags."""
        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        result = await self.db.execute(stmt)
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise AgentEngineError(f"Tenant {tenant_id} not found")

        current = tenant.features or {}
        current.update(features)
        tenant.features = current
        await self.db.flush()
        return {"id": tenant.id, "features": tenant.features}

    async def update_quota(self, tenant_id: str, max_agents: int) -> dict:
        """Update tenant agent quota."""
        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        result = await self.db.execute(stmt)
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise AgentEngineError(f"Tenant {tenant_id} not found")

        tenant.max_agents = max_agents
        await self.db.flush()
        return {"id": tenant.id, "max_agents": tenant.max_agents}
