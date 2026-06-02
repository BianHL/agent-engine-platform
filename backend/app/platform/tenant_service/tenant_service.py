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

    async def list(self) -> list[dict]:
        """List all tenants."""
        stmt = select(TenantModel)
        result = await self.db.execute(stmt)
        tenants = result.scalars().all()
        return [self._to_dict(t) for t in tenants]

    async def get(self, tenant_id: str) -> Optional[dict]:
        """Get tenant by ID."""
        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        result = await self.db.execute(stmt)
        tenant = result.scalar_one_or_none()
        if not tenant:
            return None
        return self._to_dict(tenant)

    def _to_dict(self, tenant: TenantModel) -> dict:
        return {
            "id": tenant.id,
            "name": tenant.name,
            "code": tenant.code,
            "description": tenant.settings.get("description") if tenant.settings else None,
            "status": tenant.status,
            "max_agents": tenant.max_agents,
            "features": tenant.features or {},
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
            "updated_at": tenant.updated_at.isoformat() if tenant.updated_at else None,
            "quota": {
                "max_agents": tenant.max_agents,
                "max_knowledge_bases": tenant.settings.get("max_knowledge_bases", 5) if tenant.settings else 5,
                "max_workflows": tenant.settings.get("max_workflows", 10) if tenant.settings else 10,
                "max_users": tenant.max_users,
                "storage_gb": tenant.max_storage_gb,
                "api_calls_per_month": tenant.settings.get("api_calls_per_month", 10000) if tenant.settings else 10000,
            },
        }

    async def update(self, tenant_id: str, data: dict) -> dict:
        """Update tenant basic info."""
        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        result = await self.db.execute(stmt)
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise AgentEngineError(f"Tenant {tenant_id} not found")
        if "name" in data:
            tenant.name = data["name"]
        if "code" in data:
            tenant.code = data["code"]
        if "status" in data:
            tenant.status = data["status"]
        if "description" in data:
            settings = tenant.settings or {}
            settings["description"] = data["description"]
            tenant.settings = settings
        if "quota" in data:
            quota = data["quota"]
            if "max_agents" in quota:
                tenant.max_agents = quota["max_agents"]
            if "max_users" in quota:
                tenant.max_users = quota["max_users"]
            if "storage_gb" in quota:
                tenant.max_storage_gb = quota["storage_gb"]
            settings = tenant.settings or {}
            for k in ["max_knowledge_bases", "max_workflows", "api_calls_per_month"]:
                if k in quota:
                    settings[k] = quota[k]
            tenant.settings = settings
        await self.db.flush()
        return self._to_dict(tenant)

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
