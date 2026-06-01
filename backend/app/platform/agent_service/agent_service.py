from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AgentEngineError
from app.models.base import AgentModel


class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, tenant_id: str, data: dict) -> dict:
        agent = AgentModel(
            tenant_id=tenant_id,
            name=data["name"],
            description=data.get("description", ""),
            model_provider=data.get("model_provider", ""),
            model_name=data.get("model_name", ""),
            model_config=data.get("model_config", {}),
            system_prompt=data.get("system_prompt", ""),
            tools=data.get("tools", []),
            knowledge_base_ids=data.get("knowledge_base_ids", []),
            safety_config=data.get("safety_config", {}),
            status="draft",
        )
        self.db.add(agent)
        await self.db.flush()
        return {"id": agent.id, "name": agent.name, "status": agent.status}

    async def get(self, agent_id: str, tenant_id: str) -> Optional[dict]:
        stmt = select(AgentModel).where(
            and_(AgentModel.id == agent_id, AgentModel.tenant_id == tenant_id)
        )
        result = await self.db.execute(stmt)
        agent = result.scalar_one_or_none()
        if not agent:
            return None
        return {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "model_provider": agent.model_provider,
            "model_name": agent.model_name,
            "model_config": agent.model_config,
            "system_prompt": agent.system_prompt,
            "tools": agent.tools,
            "knowledge_base_ids": agent.knowledge_base_ids,
            "safety_config": agent.safety_config,
            "status": agent.status,
            "version": agent.version,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
        }

    async def list(self, tenant_id: str, page: int = 1, size: int = 20) -> dict:
        count_result = await self.db.execute(
            select(func.count()).where(AgentModel.tenant_id == tenant_id)
        )
        total = count_result.scalar()

        stmt = (
            select(AgentModel)
            .where(AgentModel.tenant_id == tenant_id)
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(stmt)
        agents = result.scalars().all()

        return {
            "items": [
                {
                    "id": a.id,
                    "name": a.name,
                    "description": a.description,
                    "status": a.status,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in agents
            ],
            "total": total,
            "page": page,
            "size": size,
        }

    async def update(self, agent_id: str, tenant_id: str, data: dict) -> dict:
        stmt = select(AgentModel).where(
            and_(AgentModel.id == agent_id, AgentModel.tenant_id == tenant_id)
        )
        result = await self.db.execute(stmt)
        agent = result.scalar_one_or_none()
        if not agent:
            raise AgentEngineError("Agent not found")

        updatable_fields = [
            "name",
            "description",
            "model_provider",
            "model_name",
            "model_config",
            "system_prompt",
            "tools",
            "knowledge_base_ids",
            "safety_config",
        ]
        for field in updatable_fields:
            if field in data:
                setattr(agent, field, data[field])

        agent.version = (agent.version or 1) + 1
        await self.db.flush()

        return {
            "id": agent.id,
            "name": agent.name,
            "status": agent.status,
            "version": agent.version,
        }

    async def publish(self, agent_id: str, tenant_id: str) -> dict:
        stmt = select(AgentModel).where(
            and_(AgentModel.id == agent_id, AgentModel.tenant_id == tenant_id)
        )
        result = await self.db.execute(stmt)
        agent = result.scalar_one_or_none()
        if not agent:
            raise AgentEngineError("Agent not found")

        agent.status = "published"
        agent.published_at = datetime.now(UTC).replace(tzinfo=None)
        await self.db.flush()
        return {"id": agent.id, "status": agent.status}

    async def delete(self, agent_id: str, tenant_id: str) -> None:
        stmt = select(AgentModel).where(
            and_(AgentModel.id == agent_id, AgentModel.tenant_id == tenant_id)
        )
        result = await self.db.execute(stmt)
        agent = result.scalar_one_or_none()
        if agent:
            await self.db.delete(agent)
            await self.db.flush()
