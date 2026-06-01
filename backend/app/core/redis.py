"""Shared async Redis client singleton."""
from __future__ import annotations

import logging
from typing import Optional

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Return the shared async Redis client (lazy-init, reused across calls)."""
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    """Close the shared Redis connection. Call on app shutdown."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
