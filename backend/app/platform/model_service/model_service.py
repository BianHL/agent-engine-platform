from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt
from app.models.base import ModelConfigModel, ModelProviderModel


class ModelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_provider(self, tenant_id: str, data: dict) -> dict:
        provider = ModelProviderModel(
            tenant_id=tenant_id,
            name=data["name"],
            provider_type=data["provider_type"],
            api_key=encrypt(data.get("api_key", "")),
            api_base=data.get("api_base", ""),
            config=data.get("config", {}),
        )
        self.db.add(provider)
        await self.db.flush()
        return {"id": provider.id, "name": provider.name}

    async def get_provider(self, provider_id: str, tenant_id: str) -> Optional[dict]:
        stmt = select(ModelProviderModel).where(
            and_(
                ModelProviderModel.id == provider_id,
                ModelProviderModel.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        provider = result.scalar_one_or_none()
        if not provider:
            return None
        return {
            "id": provider.id,
            "name": provider.name,
            "provider_type": provider.provider_type,
            "api_base": provider.api_base,
            "config": provider.config,
            "status": provider.status,
            "created_at": provider.created_at.isoformat() if provider.created_at else None,
        }

    async def list_providers(self, tenant_id: str) -> list:
        stmt = select(ModelProviderModel).where(
            ModelProviderModel.tenant_id == tenant_id
        )
        result = await self.db.execute(stmt)
        return [
            {
                "id": p.id,
                "name": p.name,
                "provider_type": p.provider_type,
                "status": p.status,
            }
            for p in result.scalars().all()
        ]

    async def delete_provider(self, provider_id: str, tenant_id: str) -> None:
        stmt = select(ModelProviderModel).where(
            and_(
                ModelProviderModel.id == provider_id,
                ModelProviderModel.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        provider = result.scalar_one_or_none()
        if provider:
            await self.db.delete(provider)
            await self.db.flush()

    async def create_model_config(self, tenant_id: str, data: dict) -> dict:
        config = ModelConfigModel(
            tenant_id=tenant_id,
            provider_id=data["provider_id"],
            model_name=data["model_name"],
            model_type=data.get("model_type", "llm"),
            display_name=data.get("display_name", data["model_name"]),
            config=data.get("config", {}),
            is_default=data.get("is_default", False),
        )
        self.db.add(config)
        await self.db.flush()
        return {"id": config.id, "model_name": config.model_name}

    async def list_model_configs(self, tenant_id: str) -> list:
        stmt = select(ModelConfigModel).where(ModelConfigModel.tenant_id == tenant_id)
        result = await self.db.execute(stmt)
        return [
            {
                "id": c.id,
                "model_name": c.model_name,
                "model_type": c.model_type,
                "display_name": c.display_name,
                "is_default": c.is_default,
                "enabled": c.enabled,
            }
            for c in result.scalars().all()
        ]

    async def set_default(self, config_id: str, tenant_id: str) -> None:
        # Clear existing defaults
        stmt = select(ModelConfigModel).where(
            and_(
                ModelConfigModel.tenant_id == tenant_id,
                ModelConfigModel.is_default == True,
            )
        )
        result = await self.db.execute(stmt)
        for c in result.scalars().all():
            c.is_default = False

        # Set new default
        stmt = select(ModelConfigModel).where(
            and_(
                ModelConfigModel.id == config_id,
                ModelConfigModel.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()
        if config:
            config.is_default = True
        await self.db.flush()

    async def delete_model_config(self, config_id: str, tenant_id: str) -> None:
        stmt = select(ModelConfigModel).where(
            and_(
                ModelConfigModel.id == config_id,
                ModelConfigModel.tenant_id == tenant_id,
            )
        )
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()
        if config:
            await self.db.delete(config)
            await self.db.flush()
