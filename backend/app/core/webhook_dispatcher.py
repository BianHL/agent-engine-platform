"""Webhook delivery engine with HMAC signing and retry logic."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import UTC, datetime
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.ssrf import is_safe_url
from app.models.base import WebhookEventModel, WebhookModel

logger = logging.getLogger(__name__)

# Supported event types
WEBHOOK_EVENT_TYPES = [
    "agent.created",
    "agent.published",
    "agent.deleted",
    "conversation.created",
    "workflow.completed",
    "document.indexed",
    "document.deleted",
]

# Retry configuration: delays in seconds (exponential backoff)
RETRY_DELAYS = [1, 4, 16]


def compute_signature(payload_bytes: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 signature for a webhook payload."""
    return hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()


async def deliver_webhook(
    webhook: WebhookModel,
    event: WebhookEventModel,
    db: AsyncSession,
) -> None:
    """Deliver a single webhook event with retry logic.

    Updates the event record with delivery status.
    """
    payload_bytes = json.dumps(event.payload, default=str).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": event.event_type,
        "X-Webhook-Delivery": event.id,
    }

    if webhook.secret:
        signature = compute_signature(payload_bytes, webhook.secret)
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    last_status = "pending"
    last_response_status: Optional[int] = None

    safe, reason = is_safe_url(webhook.url)
    if not safe:
        logger.error("Webhook %s URL blocked: %s", webhook.id, reason)
        event.status = "blocked"
        event.response_status = 0
        await db.flush()
        return

    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook.url,
                    content=payload_bytes,
                    headers=headers,
                )
                last_response_status = response.status_code

                if 200 <= response.status_code < 300:
                    last_status = "delivered"
                    event.delivered_at = datetime.now(UTC).replace(tzinfo=None)
                    break
                else:
                    last_status = "failed"
                    logger.warning(
                        "Webhook %s delivery attempt %d returned %d",
                        webhook.id,
                        attempt + 1,
                        response.status_code,
                    )
        except Exception as exc:
            last_status = "failed"
            logger.warning(
                "Webhook %s delivery attempt %d error: %s",
                webhook.id,
                attempt + 1,
                exc,
            )

        # Wait before retry (skip wait after last attempt)
        if attempt < len(RETRY_DELAYS):
            await asyncio.sleep(RETRY_DELAYS[attempt])

    event.status = last_status
    event.retry_count = len(RETRY_DELAYS)
    event.response_status = last_response_status
    await db.flush()


async def dispatch_webhook(
    event_type: str,
    payload: dict,
    tenant_id: str,
) -> None:
    """Find matching webhooks for a tenant and enqueue delivery.

    This runs delivery tasks concurrently in the background.
    """
    async with async_session() as db:
        stmt = select(WebhookModel).where(
            WebhookModel.tenant_id == tenant_id,
            WebhookModel.enabled == True,  # noqa: E712
        )
        result = await db.execute(stmt)
        webhooks = result.scalars().all()

        # Filter to webhooks subscribed to this event type
        matching = [
            wh for wh in webhooks
            if not wh.events or event_type in wh.events
        ]

        if not matching:
            return

        # Create event records and deliver
        tasks = []
        for webhook in matching:
            event = WebhookEventModel(
                webhook_id=webhook.id,
                event_type=event_type,
                payload=payload,
                status="pending",
            )
            db.add(event)
            await db.flush()

            tasks.append(deliver_webhook(webhook, event, db))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
