"""Debug session storage with Redis backend and in-memory fallback."""
import json
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class DebugSessionStore:
    """Store debug sessions with Redis backend."""

    def __init__(self, redis_client=None, prefix: str = "debug:session:", ttl: int = 3600):
        self._redis = redis_client
        self._prefix = prefix
        self._ttl = ttl
        self._memory_fallback: dict[str, dict] = {}

    async def get(self, workflow_id: str) -> Optional[dict]:
        key = f"{self._prefix}{workflow_id}"

        if self._redis:
            try:
                data = await self._redis.get(key)
                if data:
                    return json.loads(data)
                return None
            except Exception as e:
                logger.warning(f"Redis get failed, using memory fallback: {e}")

        entry = self._memory_fallback.get(workflow_id)
        if entry and time.time() - entry.get("_stored_at", 0) < self._ttl:
            return entry
        elif entry:
            del self._memory_fallback[workflow_id]
        return None

    async def set(self, workflow_id: str, session_data: dict):
        key = f"{self._prefix}{workflow_id}"
        session_data["_stored_at"] = time.time()

        if self._redis:
            try:
                await self._redis.setex(key, self._ttl, json.dumps(session_data, default=str))
                return
            except Exception as e:
                logger.warning(f"Redis set failed, using memory fallback: {e}")

        self._memory_fallback[workflow_id] = session_data

    async def delete(self, workflow_id: str):
        key = f"{self._prefix}{workflow_id}"

        if self._redis:
            try:
                await self._redis.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")

        self._memory_fallback.pop(workflow_id, None)

    async def list_active(self) -> list[str]:
        if self._redis:
            try:
                keys = await self._redis.keys(f"{self._prefix}*")
                return [k.decode().replace(self._prefix, "") for k in keys]
            except Exception as e:
                logger.warning(f"Redis keys failed: {e}")

        return list(self._memory_fallback.keys())

    def set_redis(self, redis_client):
        """Set Redis client after initialization."""
        self._redis = redis_client


# Global instance
_debug_store: Optional[DebugSessionStore] = None


def get_debug_store() -> DebugSessionStore:
    global _debug_store
    if _debug_store is None:
        _debug_store = DebugSessionStore()
    return _debug_store


def init_debug_store(redis_client=None) -> DebugSessionStore:
    global _debug_store
    _debug_store = DebugSessionStore(redis_client=redis_client)
    return _debug_store
