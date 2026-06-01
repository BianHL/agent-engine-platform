"""Tests for DebugSessionStore."""
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.engines.workflow_engine.debug_store import (
    DebugSessionStore,
    get_debug_store,
    init_debug_store,
)


class TestDebugSessionStoreMemoryFallback:
    """Test in-memory fallback when no Redis client is provided."""

    @pytest.fixture
    def store(self):
        return DebugSessionStore(redis_client=None, ttl=60)

    @pytest.mark.asyncio
    async def test_set_and_get(self, store):
        session_data = {"mode": "record", "breakpoints": ["node1"]}
        await store.set("wf-1", session_data)

        result = await store.get("wf-1")
        assert result is not None
        assert result["mode"] == "record"
        assert result["breakpoints"] == ["node1"]
        assert "_stored_at" in result

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, store):
        result = await store.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, store):
        await store.set("wf-1", {"mode": "record"})
        await store.delete("wf-1")

        result = await store.get("wf-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store):
        await store.delete("nonexistent")

    @pytest.mark.asyncio
    async def test_list_active(self, store):
        await store.set("wf-1", {"mode": "record"})
        await store.set("wf-2", {"mode": "breakpoint"})

        active = await store.list_active()
        assert set(active) == {"wf-1", "wf-2"}

    @pytest.mark.asyncio
    async def test_list_active_empty(self, store):
        active = await store.list_active()
        assert active == []

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        store = DebugSessionStore(redis_client=None, ttl=1)
        await store.set("wf-1", {"mode": "record"})

        result = await store.get("wf-1")
        assert result is not None

        await asyncio.sleep(1.1)

        result = await store.get("wf-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_stored_at_timestamp(self, store):
        before = time.time()
        await store.set("wf-1", {"mode": "record"})
        after = time.time()

        result = await store.get("wf-1")
        assert before <= result["_stored_at"] <= after

    @pytest.mark.asyncio
    async def test_set_updates_existing(self, store):
        await store.set("wf-1", {"mode": "record"})
        await store.set("wf-1", {"mode": "breakpoint"})

        result = await store.get("wf-1")
        assert result["mode"] == "breakpoint"


class TestDebugSessionStoreRedis:
    """Test Redis backend with mocked Redis client."""

    @pytest.fixture
    def mock_redis(self):
        redis = AsyncMock()
        redis.get = AsyncMock()
        redis.setex = AsyncMock()
        redis.delete = AsyncMock()
        redis.keys = AsyncMock()
        return redis

    @pytest.fixture
    def store(self, mock_redis):
        return DebugSessionStore(redis_client=mock_redis, prefix="test:", ttl=3600)

    @pytest.mark.asyncio
    async def test_get_from_redis(self, store, mock_redis):
        session_data = {"mode": "record", "breakpoints": ["node1"]}
        mock_redis.get.return_value = json.dumps(session_data).encode()

        result = await store.get("wf-1")
        assert result == session_data
        mock_redis.get.assert_called_once_with("test:wf-1")

    @pytest.mark.asyncio
    async def test_get_returns_none_when_empty(self, store, mock_redis):
        mock_redis.get.return_value = None

        result = await store.get("wf-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_to_redis(self, store, mock_redis):
        session_data = {"mode": "record"}
        await store.set("wf-1", session_data)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "test:wf-1"
        assert call_args[0][1] == 3600
        stored_data = json.loads(call_args[0][2])
        assert stored_data["mode"] == "record"
        assert "_stored_at" in stored_data

    @pytest.mark.asyncio
    async def test_delete_from_redis(self, store, mock_redis):
        await store.delete("wf-1")
        mock_redis.delete.assert_called_once_with("test:wf-1")

    @pytest.mark.asyncio
    async def test_list_active_from_redis(self, store, mock_redis):
        mock_redis.keys.return_value = [b"test:wf-1", b"test:wf-2"]

        active = await store.list_active()
        assert active == ["wf-1", "wf-2"]
        mock_redis.keys.assert_called_once_with("test:*")

    @pytest.mark.asyncio
    async def test_redis_get_failure_falls_back_to_memory(self, store, mock_redis):
        mock_redis.get.side_effect = Exception("Connection refused")

        result = await store.get("wf-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_redis_set_failure_falls_back_to_memory(self, store, mock_redis):
        mock_redis.setex.side_effect = Exception("Connection refused")

        await store.set("wf-1", {"mode": "record"})
        result = await store.get("wf-1")
        assert result is not None
        assert result["mode"] == "record"

    @pytest.mark.asyncio
    async def test_redis_delete_failure_falls_back_to_memory(self, store, mock_redis):
        mock_redis.delete.side_effect = Exception("Connection refused")
        store._memory_fallback["wf-1"] = {"mode": "record"}

        await store.delete("wf-1")
        assert "wf-1" not in store._memory_fallback

    @pytest.mark.asyncio
    async def test_redis_keys_failure_falls_back_to_memory(self, store, mock_redis):
        mock_redis.keys.side_effect = Exception("Connection refused")
        store._memory_fallback["wf-1"] = {"mode": "record"}

        active = await store.list_active()
        assert active == ["wf-1"]


class TestDebugSessionStoreRedisSerialization:
    """Test JSON serialization edge cases."""

    @pytest.fixture
    def store(self):
        return DebugSessionStore(redis_client=None, ttl=60)

    @pytest.mark.asyncio
    async def test_serializes_complex_data(self, store):
        session_data = {
            "mode": "breakpoint",
            "breakpoints": ["node1", "node2"],
            "history": [
                {"node_id": "n1", "status": "success", "timestamp": "2024-01-01T00:00:00Z"},
                {"node_id": "n2", "status": "failed", "error": "timeout"},
            ],
        }
        await store.set("wf-1", session_data)

        result = await store.get("wf-1")
        assert result["mode"] == "breakpoint"
        assert len(result["history"]) == 2
        assert result["history"][0]["node_id"] == "n1"


class TestDebugSessionStoreGlobalInstance:
    """Test global store initialization and retrieval."""

    def test_get_debug_store_creates_instance(self):
        import app.engines.workflow_engine.debug_store as module
        module._debug_store = None

        store = get_debug_store()
        assert isinstance(store, DebugSessionStore)

    def test_get_debug_store_returns_same_instance(self):
        import app.engines.workflow_engine.debug_store as module
        module._debug_store = None

        store1 = get_debug_store()
        store2 = get_debug_store()
        assert store1 is store2

    def test_init_debug_store_with_redis(self):
        mock_redis = AsyncMock()
        store = init_debug_store(redis_client=mock_redis)
        assert store._redis is mock_redis

    def test_init_debug_store_without_redis(self):
        store = init_debug_store()
        assert store._redis is None


class TestDebugSessionStoreSetRedis:
    """Test setting Redis client after initialization."""

    def test_set_redis(self):
        store = DebugSessionStore()
        assert store._redis is None

        mock_redis = AsyncMock()
        store.set_redis(mock_redis)
        assert store._redis is mock_redis
