"""Publish channels API."""
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.rbac import require_permission
from app.models.agent import AgentModel
from app.models.publish_channel import PublishChannelModel

router = APIRouter(prefix="/publish", tags=["publish"])


class CreateChannelRequest(BaseModel):
    agent_id: str
    type: str
    name: str
    config: dict = {}


class UpdateChannelRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    config: Optional[dict] = None


def _channel_to_dict(channel: PublishChannelModel, include_key: bool = False) -> dict:
    result = {
        "id": channel.id,
        "agent_id": channel.agent_id,
        "type": channel.type,
        "name": channel.name,
        "status": channel.status,
        "config": channel.config,
        "api_key_prefix": channel.api_key_prefix,
        "total_calls": channel.total_calls,
        "calls_today": channel.calls_today,
        "created_at": str(channel.created_at) if channel.created_at else None,
    }
    if not include_key and "api_key" in result.get("config", {}):
        result["config"] = {k: v for k, v in result["config"].items() if k != "api_key"}
    return result


@router.get("/channels")
async def list_channels(
    agent_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    stmt = select(PublishChannelModel).where(
        PublishChannelModel.tenant_id == user["tenant_id"])
    if agent_id:
        stmt = stmt.where(PublishChannelModel.agent_id == agent_id)
    result = await db.execute(stmt)
    channels = result.scalars().all()
    return [_channel_to_dict(c) for c in channels]


@router.post("/channels", status_code=status.HTTP_201_CREATED)
async def create_channel(
    body: CreateChannelRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("agent", "update"))):
    stmt = select(AgentModel).where(
        AgentModel.id == body.agent_id,
        AgentModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    api_key_prefix = None
    config = dict(body.config)
    if body.type == "api":
        raw_key = secrets.token_urlsafe(32)
        api_key_prefix = raw_key[:8]
        config["api_key"] = raw_key
        config["endpoint"] = "/api/v1/chat/completions"

    channel = PublishChannelModel(
        tenant_id=user["tenant_id"],
        agent_id=body.agent_id,
        type=body.type,
        name=body.name,
        status="active",
        config=config,
        api_key_prefix=api_key_prefix)
    db.add(channel)
    await db.flush()

    return _channel_to_dict(channel, include_key=body.type == "api")


@router.put("/channels/{channel_id}")
async def update_channel(
    channel_id: str,
    body: UpdateChannelRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("agent", "update"))):
    stmt = select(PublishChannelModel).where(
        PublishChannelModel.id == channel_id,
        PublishChannelModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    if body.name is not None:
        channel.name = body.name
    if body.status is not None:
        channel.status = body.status
    if body.config is not None:
        channel.config = body.config

    await db.flush()
    return _channel_to_dict(channel)


@router.delete("/channels/{channel_id}")
async def delete_channel(
    channel_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("agent", "delete"))):
    stmt = select(PublishChannelModel).where(
        PublishChannelModel.id == channel_id,
        PublishChannelModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    await db.delete(channel)
    await db.flush()
    return {"status": "deleted"}


@router.get("/channels/{channel_id}/stats")
async def get_channel_stats(
    channel_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("agent", "delete"))):
    stmt = select(PublishChannelModel).where(
        PublishChannelModel.id == channel_id,
        PublishChannelModel.tenant_id == user["tenant_id"])
    result = await db.execute(stmt)
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    return {
        "channel_id": channel.id,
        "total_calls": channel.total_calls,
        "calls_today": channel.calls_today,
    }
