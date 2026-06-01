"""Webhook management API endpoints."""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.rbac import require_permission
from app.core.ssrf import is_safe_url
from app.core.webhook_dispatcher import WEBHOOK_EVENT_TYPES, dispatch_webhook
from app.models.base import WebhookEventModel, WebhookModel
from app.schemas.api import (
    CreateWebhookRequest,
    WebhookEventResponse,
    WebhookResponse,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_webhook(
    body: CreateWebhookRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("webhook", "create")),
):
    """Register a new webhook."""
    # Validate event types
    invalid = [e for e in body.events if e not in WEBHOOK_EVENT_TYPES]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event types: {', '.join(invalid)}. "
                   f"Supported: {', '.join(WEBHOOK_EVENT_TYPES)}",
        )

    safe, reason = is_safe_url(body.url)
    if not safe:
        raise HTTPException(status_code=400, detail=f"Webhook URL not allowed: {reason}")

    webhook = WebhookModel(
        tenant_id=user["tenant_id"],
        name=body.name,
        url=body.url,
        secret=body.secret,
        events=body.events,
        enabled=True,
    )
    db.add(webhook)
    await db.flush()

    return {
        "id": webhook.id,
        "name": webhook.name,
        "url": webhook.url,
        "events": webhook.events or [],
        "enabled": webhook.enabled,
        "created_at": webhook.created_at.isoformat() if webhook.created_at else None,
        "updated_at": webhook.updated_at.isoformat() if webhook.updated_at else None,
    }


@router.get("/")
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List webhooks for the current tenant."""
    stmt = (
        select(WebhookModel)
        .where(WebhookModel.tenant_id == user["tenant_id"])
        .order_by(WebhookModel.created_at.desc())
    )
    result = await db.execute(stmt)
    webhooks = result.scalars().all()

    return [
        {
            "id": w.id,
            "name": w.name,
            "url": w.url,
            "events": w.events or [],
            "enabled": w.enabled,
            "created_at": w.created_at.isoformat() if w.created_at else None,
            "updated_at": w.updated_at.isoformat() if w.updated_at else None,
        }
        for w in webhooks
    ]


@router.put("/{webhook_id}")
async def update_webhook(
    webhook_id: str,
    body: CreateWebhookRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("webhook", "update")),
):
    """Update a webhook."""
    stmt = select(WebhookModel).where(
        WebhookModel.id == webhook_id,
        WebhookModel.tenant_id == user["tenant_id"],
    )
    result = await db.execute(stmt)
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    invalid = [e for e in body.events if e not in WEBHOOK_EVENT_TYPES]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event types: {', '.join(invalid)}",
        )

    safe, reason = is_safe_url(body.url)
    if not safe:
        raise HTTPException(status_code=400, detail=f"Webhook URL not allowed: {reason}")

    webhook.name = body.name
    webhook.url = body.url
    webhook.secret = body.secret
    webhook.events = body.events
    await db.flush()

    return {
        "id": webhook.id,
        "name": webhook.name,
        "url": webhook.url,
        "events": webhook.events or [],
        "enabled": webhook.enabled,
        "created_at": webhook.created_at.isoformat() if webhook.created_at else None,
        "updated_at": webhook.updated_at.isoformat() if webhook.updated_at else None,
    }


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("webhook", "delete")),
):
    """Delete a webhook."""
    stmt = select(WebhookModel).where(
        WebhookModel.id == webhook_id,
        WebhookModel.tenant_id == user["tenant_id"],
    )
    result = await db.execute(stmt)
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    await db.delete(webhook)
    await db.flush()
    return None


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Send a test event to a webhook."""
    stmt = select(WebhookModel).where(
        WebhookModel.id == webhook_id,
        WebhookModel.tenant_id == user["tenant_id"],
    )
    result = await db.execute(stmt)
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    test_payload = {
        "event": "webhook.test",
        "timestamp": datetime.now(UTC).isoformat(),
        "data": {"message": "This is a test webhook delivery."},
    }

    await dispatch_webhook(
        event_type="webhook.test",
        payload=test_payload,
        tenant_id=user["tenant_id"],
    )

    return {"status": "test_event_sent"}


@router.get("/{webhook_id}/events")
async def list_webhook_events(
    webhook_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List delivery history for a webhook."""
    # Verify webhook belongs to tenant
    stmt = select(WebhookModel).where(
        WebhookModel.id == webhook_id,
        WebhookModel.tenant_id == user["tenant_id"],
    )
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Webhook not found")

    stmt = (
        select(WebhookEventModel)
        .where(WebhookEventModel.webhook_id == webhook_id)
        .order_by(WebhookEventModel.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    return [
        {
            "id": e.id,
            "webhook_id": e.webhook_id,
            "event_type": e.event_type,
            "payload": e.payload or {},
            "status": e.status,
            "retry_count": e.retry_count,
            "response_status": e.response_status,
            "delivered_at": e.delivered_at.isoformat() if e.delivered_at else None,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]
