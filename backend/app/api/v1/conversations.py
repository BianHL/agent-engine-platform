"""Conversation management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.rbac import require_permission
from app.core.database import get_db
from app.platform.conversation_service.conversation_service import ConversationService
from app.schemas.api import (
    AddMessageRequest,
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
    PaginatedResponse,
    StatusResponse)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/")
async def list_conversations(
    agent_id: str = Query(None, description="Filter by agent ID"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """List conversations for the current user, optionally filtered by agent."""
    svc = ConversationService(db)
    return await svc.list_conversations(
        tenant_id=user["tenant_id"],
        user_id=user["id"],
        agent_id=agent_id,
        page=page,
        size=size)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: CreateConversationRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("conversation", "create"))):
    """Create a new conversation."""
    svc = ConversationService(db)
    result = await svc.create(
        tenant_id=user["tenant_id"],
        user_id=user["id"],
        agent_id=body.agent_id,
        title=body.title or "")
    return result


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get a conversation by ID."""
    svc = ConversationService(db)
    result = await svc.get(conversation_id, tenant_id=user["tenant_id"])
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("conversation", "delete"))):
    """Delete a conversation and all its messages."""
    svc = ConversationService(db)
    await svc.delete(conversation_id, tenant_id=user["tenant_id"])
    return None


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    """Get all messages for a conversation."""
    svc = ConversationService(db)
    # Verify conversation exists and belongs to tenant
    conv = await svc.get(conversation_id, tenant_id=user["tenant_id"])
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await svc.get_messages(conversation_id, tenant_id=user["tenant_id"])


@router.post("/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def add_message(
    conversation_id: str,
    body: AddMessageRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("conversation", "create"))):
    """Add a message to a conversation."""
    svc = ConversationService(db)
    # Verify conversation exists and belongs to tenant
    conv = await svc.get(conversation_id, tenant_id=user["tenant_id"])
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    result = await svc.add_message(
        conversation_id=conversation_id,
        role=body.role,
        content=body.content,
        tenant_id=user["tenant_id"],
        metadata=body.metadata)
    return result
