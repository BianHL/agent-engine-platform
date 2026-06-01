from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, get_tenant_id
from app.core.database import get_db
from app.core.rbac import require_permission
from app.platform.agent_service.agent_service import AgentService
from app.schemas.api import (
    AgentResponse,
    CreateAgentRequest,
    PaginatedResponse,
    StatusResponse,
    UpdateAgentRequest)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_agent(
    body: CreateAgentRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("agent", "create"))):
    """Create a new agent."""
    svc = AgentService(db)
    return await svc.create(tenant_id=user["tenant_id"], data=body.model_dump())


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get an agent by ID."""
    svc = AgentService(db)
    result = await svc.get(agent_id, tenant_id=user["tenant_id"])
    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")
    return result


@router.get("/")
async def list_agents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """List agents for the current tenant."""
    svc = AgentService(db)
    return await svc.list(tenant_id=user["tenant_id"], page=page, size=size)


@router.put("/{agent_id}")
async def update_agent(
    agent_id: str,
    body: UpdateAgentRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("agent", "update"))):
    """Update an agent."""
    svc = AgentService(db)
    return await svc.update(
        agent_id,
        tenant_id=user["tenant_id"],
        data=body.model_dump(exclude_unset=True))


@router.post("/{agent_id}/publish")
async def publish_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("agent", "publish"))):
    """Publish an agent (draft -> published)."""
    svc = AgentService(db)
    return await svc.publish(agent_id, tenant_id=user["tenant_id"])


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("agent", "delete"))):
    """Delete an agent."""
    svc = AgentService(db)
    await svc.delete(agent_id, tenant_id=user["tenant_id"])
    return {"status": "deleted"}
