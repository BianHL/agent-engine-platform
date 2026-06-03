"""Integration tests for long-term memory expiration and degradation (R-008).

Verifies that memory entries can expire and that the system handles
expired memories gracefully across all three tiers.
"""
import asyncio
import json
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.engines.memory_engine.memory import (
    ShortTermMemory,
    LongTermMemory,
    WorkingMemory,
    MemoryEngine,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_redis(list_data=None, string_data=None):
    """Create a mock Redis client with configurable return values."""
    redis = AsyncMock()
    redis.lpush = AsyncMock()
    redis.ltrim = AsyncMock()
    redis.expire = AsyncMock()
    redis.lrange = AsyncMock(return_value=[
        json.dumps({"role": "user", "content": f"msg{i}", "timestamp": 1000 + i})
        for i in range(list_data or 0)
    ])
    redis.delete = AsyncMock()
    redis.get = AsyncMock(return_value=string_data)
    redis.set = AsyncMock()
    return redis


# ---------------------------------------------------------------------------
# 1. Short-term memory TTL expiration with real-time simulation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_short_term_ttl_expires_after_duration():
    """Short-term memory sets TTL matching configured duration (R-003/R-008).

    Verifies that the expire call uses the exact TTL value so Redis will
    evict the key after the configured window.
    """
    ttl_seconds = 2
    redis = _make_mock_redis()
    stm = ShortTermMemory(redis, max_messages=20, ttl=ttl_seconds)

    await stm.add_message("sess_ttl", "user", "hello")

    redis.expire.assert_called_once_with("memory:short:sess_ttl", ttl_seconds)


@pytest.mark.asyncio
async def test_short_term_retrieval_after_expiry_returns_empty():
    """After TTL expiry, Redis lrange returns empty list.

    Simulates the situation where the key has expired in Redis and
    get_messages should return an empty list gracefully.
    """
    redis = _make_mock_redis(list_data=0)  # empty list after expiry
    stm = ShortTermMemory(redis, max_messages=20, ttl=1)

    messages = await stm.get_messages("sess_expired")

    assert messages == []
    redis.lrange.assert_called_once_with("memory:short:sess_expired", 0, 19)


@pytest.mark.asyncio
async def test_short_term_ttl_refreshed_on_each_add():
    """Each add_message resets the TTL, extending the expiry window."""
    redis = _make_mock_redis()
    stm = ShortTermMemory(redis, max_messages=20, ttl=60)

    for i in range(3):
        await stm.add_message("sess_refresh", "user", f"msg{i}")

    assert redis.expire.call_count == 3
    for call in redis.expire.call_args_list:
        assert call[0] == ("memory:short:sess_refresh", 60)


# ---------------------------------------------------------------------------
# 2. Long-term memory search returns empty for expired / missing entries
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_long_term_search_returns_empty_when_vector_store_empty():
    """Long-term memory search returns [] when vector store has no results."""
    embedding = AsyncMock()
    embedding.embed = AsyncMock(return_value=[[0.1] * 1536])
    vector_store = AsyncMock()
    vector_store.search = AsyncMock(return_value=[])

    ltm = LongTermMemory(
        db_session=AsyncMock(),
        vector_store=vector_store,
        embedding_adapter=embedding,
    )

    results = await ltm.search("test query", "t1", "u1")

    assert results == []


@pytest.mark.asyncio
async def test_long_term_search_filters_by_user_id():
    """Search results not matching the user_id are excluded."""
    embedding = AsyncMock()
    embedding.embed = AsyncMock(return_value=[[0.1] * 1536])
    vector_store = AsyncMock()
    vector_store.search = AsyncMock(return_value=[
        {"id": "1", "score": 0.9, "content": "match", "metadata": {"user_id": "u1"}},
        {"id": "2", "score": 0.8, "content": "other user", "metadata": {"user_id": "u2"}},
        {"id": "3", "score": 0.7, "content": "match again", "metadata": {"user_id": "u1"}},
    ])

    ltm = LongTermMemory(
        db_session=AsyncMock(),
        vector_store=vector_store,
        embedding_adapter=embedding,
    )

    results = await ltm.search("query", "t1", "u1")

    assert len(results) == 2
    assert all(r["metadata"]["user_id"] == "u1" for r in results)


@pytest.mark.asyncio
async def test_long_term_search_handles_embedding_failure():
    """Search returns empty list when embedding fails (graceful degradation)."""
    embedding = AsyncMock()
    embedding.embed = AsyncMock(return_value=None)
    vector_store = AsyncMock()

    ltm = LongTermMemory(
        db_session=AsyncMock(),
        vector_store=vector_store,
        embedding_adapter=embedding,
    )

    results = await ltm.search("query", "t1", "u1")

    assert results == []
    vector_store.search.assert_not_called()


@pytest.mark.asyncio
async def test_long_term_search_handles_vector_store_exception():
    """Search returns empty list when vector store raises (graceful degradation)."""
    embedding = AsyncMock()
    embedding.embed = AsyncMock(return_value=[[0.1] * 1536])
    vector_store = AsyncMock()
    vector_store.search = AsyncMock(side_effect=RuntimeError("connection lost"))

    ltm = LongTermMemory(
        db_session=AsyncMock(),
        vector_store=vector_store,
        embedding_adapter=embedding,
    )

    results = await ltm.search("query", "t1", "u1")

    assert results == []


# ---------------------------------------------------------------------------
# 3. Memory context assembly degrades gracefully when long-term unavailable
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_context_with_no_long_term_memory():
    """Context assembly works when long-term memory is None (R-008)."""
    redis = _make_mock_redis(list_data=2, string_data="Working summary")
    engine = MemoryEngine(redis_client=redis)  # no db/vector_store -> long_term is None

    ctx = await engine.get_context("sess1", "t1", "u1", "test query")

    assert ctx["short_term"] is not None
    assert ctx["working_summary"] == "Working summary"
    assert ctx["relevant_memories"] == []


@pytest.mark.asyncio
async def test_get_context_with_empty_query_skips_long_term():
    """Empty query skips long-term search even when available."""
    redis = _make_mock_redis(list_data=1, string_data=None)
    vector_store = AsyncMock()
    vector_store.search = AsyncMock(return_value=[])

    engine = MemoryEngine(
        redis_client=redis,
        db_session=AsyncMock(),
        vector_store=vector_store,
        embedding_adapter=AsyncMock(),
    )

    ctx = await engine.get_context("sess1", "t1", "u1", "")

    assert ctx["relevant_memories"] == []
    vector_store.search.assert_not_called()


@pytest.mark.asyncio
async def test_get_context_short_term_empty_long_term_unavailable():
    """Context degrades to empty when both short-term and long-term are unavailable."""
    redis = _make_mock_redis(list_data=0, string_data=None)
    engine = MemoryEngine(redis_client=redis)

    ctx = await engine.get_context("sess_new", "t1", "u1", "query")

    assert ctx["short_term"] == []
    assert ctx["working_summary"] == ""
    assert ctx["relevant_memories"] == []


@pytest.mark.asyncio
async def test_get_context_long_term_search_failure_does_not_break_assembly():
    """Long-term search failure is caught; context still returns short-term + summary."""
    redis = _make_mock_redis(list_data=3, string_data="Summary text")
    embedding = AsyncMock()
    embedding.embed = AsyncMock(side_effect=RuntimeError("embedding service down"))
    vector_store = AsyncMock()

    engine = MemoryEngine(
        redis_client=redis,
        db_session=AsyncMock(),
        vector_store=vector_store,
        embedding_adapter=embedding,
    )

    ctx = await engine.get_context("sess1", "t1", "u1", "test query")

    assert len(ctx["short_term"]) == 3
    assert ctx["working_summary"] == "Summary text"
    assert ctx["relevant_memories"] == []


# ---------------------------------------------------------------------------
# 4. Memory cleanup removes expired entries
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_clear_session_deletes_short_term_key():
    """clear_session deletes the Redis key for short-term memory."""
    redis = _make_mock_redis()
    engine = MemoryEngine(redis_client=redis)

    await engine.clear_session("sess_cleanup")

    # clear_session deletes 3 keys: short-term, working, and summary
    assert redis.delete.call_count == 3


@pytest.mark.asyncio
async def test_clear_session_idempotent():
    """Clearing an already-cleared session does not raise."""
    redis = _make_mock_redis()
    engine = MemoryEngine(redis_client=redis)

    await engine.clear_session("sess_cleanup")
    await engine.clear_session("sess_cleanup")

    # Each call deletes 3 keys, so 2 calls = 6
    assert redis.delete.call_count == 6


@pytest.mark.asyncio
async def test_short_term_clear_calls_delete():
    """ShortTermMemory.clear delegates to redis.delete."""
    redis = _make_mock_redis()
    stm = ShortTermMemory(redis, max_messages=20, ttl=3600)

    await stm.clear("sess_xyz")

    redis.delete.assert_called_once_with("memory:short:sess_xyz")


@pytest.mark.asyncio
async def test_working_memory_summary_expires_via_redis_ttl():
    """Working memory sets Redis ex=7200, ensuring auto-expiry."""
    redis = _make_mock_redis()
    llm = AsyncMock()
    llm.chat = AsyncMock(return_value=MagicMock(content="Compressed summary"))

    wm = WorkingMemory(redis, max_tokens=2000)
    messages = [{"role": "user", "content": f"msg{i}"} for i in range(10)]
    await wm.compress("sess1", messages, llm)

    _, kwargs = redis.set.call_args
    assert kwargs.get("ex") == 7200


# ---------------------------------------------------------------------------
# 5. Working memory compression handles empty / edge-case context
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_working_memory_compress_empty_messages():
    """Compression with empty message list does nothing."""
    redis = _make_mock_redis()
    llm = AsyncMock()

    wm = WorkingMemory(redis, max_tokens=2000)
    await wm.compress("sess_empty", [], llm)

    llm.chat.assert_not_called()
    redis.set.assert_not_called()


@pytest.mark.asyncio
async def test_working_memory_compress_below_threshold():
    """Compression is skipped when message count < 5."""
    redis = _make_mock_redis()
    llm = AsyncMock()

    wm = WorkingMemory(redis, max_tokens=2000)
    messages = [{"role": "user", "content": "msg"}] * 4
    await wm.compress("sess_short", messages, llm)

    llm.chat.assert_not_called()
    redis.set.assert_not_called()


@pytest.mark.asyncio
async def test_working_memory_compress_no_llm_adapter():
    """Compression is skipped when llm_adapter is None."""
    redis = _make_mock_redis()

    wm = WorkingMemory(redis, max_tokens=2000)
    messages = [{"role": "user", "content": f"msg{i}"} for i in range(10)]
    await wm.compress("sess_nollm", messages, llm_adapter=None)

    redis.set.assert_not_called()


@pytest.mark.asyncio
async def test_working_memory_compress_llm_failure_is_swallowed():
    """LLM failure during compression is caught; no exception propagates."""
    redis = _make_mock_redis()
    llm = AsyncMock()
    llm.chat = AsyncMock(side_effect=RuntimeError("LLM unavailable"))

    wm = WorkingMemory(redis, max_tokens=2000)
    messages = [{"role": "user", "content": f"msg{i}"} for i in range(10)]

    # Should not raise
    await wm.compress("sess_fail", messages, llm)

    redis.set.assert_not_called()


@pytest.mark.asyncio
async def test_working_memory_get_summary_expired_returns_empty():
    """get_summary returns '' when Redis key has expired (returns None)."""
    redis = _make_mock_redis(string_data=None)
    wm = WorkingMemory(redis)

    summary = await wm.get_summary("sess_expired")

    assert summary == ""


@pytest.mark.asyncio
async def test_working_memory_compress_exactly_at_threshold():
    """Compression triggers at exactly 5 messages (the boundary)."""
    redis = _make_mock_redis()
    llm = AsyncMock()
    llm.chat = AsyncMock(return_value=MagicMock(content="Compressed at boundary"))

    wm = WorkingMemory(redis, max_tokens=2000)
    messages = [{"role": "user", "content": f"msg{i}"} for i in range(5)]
    await wm.compress("sess_boundary", messages, llm)

    llm.chat.assert_called_once()
    redis.set.assert_called_once()
