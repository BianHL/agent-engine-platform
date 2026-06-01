"""Unit tests for Memory Engine - TTL, capacity, and context assembly."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.engines.memory_engine.memory import (
    ShortTermMemory,
    LongTermMemory,
    WorkingMemory,
    MemoryEngine,
)


def _make_mock_redis(list_data=None, string_data=None):
    """Create a mock Redis client."""
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


# === Short-Term Memory Tests ===

@pytest.mark.asyncio
async def test_short_term_add_message():
    """Adding a message calls LPUSH, LTRIM, EXPIRE."""
    redis = _make_mock_redis()
    stm = ShortTermMemory(redis, max_messages=20, ttl=3600)
    await stm.add_message("sess1", "user", "hello")
    redis.lpush.assert_called_once()
    redis.ltrim.assert_called_once_with("memory:short:sess1", 0, 19)
    redis.expire.assert_called_once_with("memory:short:sess1", 3600)


@pytest.mark.asyncio
async def test_short_term_capacity_limit():
    """Only max_messages are kept (R-002)."""
    redis = _make_mock_redis()
    stm = ShortTermMemory(redis, max_messages=20, ttl=3600)
    # Add 25 messages
    for i in range(25):
        await stm.add_message("sess1", "user", f"msg{i}")
    # LTRIM is called with 0, max_messages-1 each time
    assert redis.ltrim.call_count == 25
    # Every call trims to max_messages
    for call in redis.ltrim.call_args_list:
        assert call[0] == ("memory:short:sess1", 0, 19)


@pytest.mark.asyncio
async def test_short_term_ttl():
    """TTL is set on every add (R-003)."""
    redis = _make_mock_redis()
    stm = ShortTermMemory(redis, max_messages=20, ttl=60)
    await stm.add_message("sess1", "user", "hello")
    redis.expire.assert_called_once_with("memory:short:sess1", 60)


@pytest.mark.asyncio
async def test_short_term_get_messages():
    """Getting messages returns parsed list."""
    redis = _make_mock_redis(list_data=3)
    stm = ShortTermMemory(redis, max_messages=20, ttl=3600)
    messages = await stm.get_messages("sess1")
    assert len(messages) == 3
    assert messages[0]["role"] == "user"


@pytest.mark.asyncio
async def test_short_term_clear():
    """Clearing session deletes the key."""
    redis = _make_mock_redis()
    stm = ShortTermMemory(redis)
    await stm.clear("sess1")
    redis.delete.assert_called_once_with("memory:short:sess1")


# === Working Memory Tests ===

@pytest.mark.asyncio
async def test_working_memory_compression():
    """Working memory compresses long conversations (R-006)."""
    redis = _make_mock_redis(string_data="Compressed summary")
    llm = AsyncMock()
    llm.chat = AsyncMock(return_value=MagicMock(content="Compressed summary"))

    wm = WorkingMemory(redis, max_tokens=2000)
    messages = [{"role": "user", "content": f"msg{i}"} for i in range(10)]
    await wm.compress("sess1", messages, llm)

    llm.chat.assert_called_once()
    redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_working_memory_skips_short_conversations():
    """Working memory skips compression for < 5 messages."""
    redis = _make_mock_redis()
    llm = AsyncMock()
    wm = WorkingMemory(redis)
    messages = [{"role": "user", "content": "msg"}] * 3
    await wm.compress("sess1", messages, llm)
    llm.chat.assert_not_called()


@pytest.mark.asyncio
async def test_working_memory_get_summary():
    """Getting summary returns stored value."""
    redis = _make_mock_redis(string_data="Summary text")
    wm = WorkingMemory(redis)
    summary = await wm.get_summary("sess1")
    assert summary == "Summary text"


@pytest.mark.asyncio
async def test_working_memory_empty_summary():
    """Getting summary when none exists returns empty string."""
    redis = _make_mock_redis(string_data=None)
    wm = WorkingMemory(redis)
    summary = await wm.get_summary("sess1")
    assert summary == ""


# === Memory Engine Integration Tests ===

@pytest.mark.asyncio
async def test_memory_engine_get_context():
    """get_context assembles short_term + working_summary + relevant (R-007)."""
    redis = _make_mock_redis(list_data=2, string_data="Summary")
    embedding = AsyncMock()
    embedding.embed = AsyncMock(return_value=[[0.1] * 1536])
    vector_store = AsyncMock()
    vector_store.search = AsyncMock(return_value=[
        {"id": "1", "score": 0.9, "content": "relevant memory", "metadata": {"user_id": "u1"}},
    ])

    engine = MemoryEngine(
        redis_client=redis,
        db_session=AsyncMock(),
        vector_store=vector_store,
        embedding_adapter=embedding,
    )
    ctx = await engine.get_context("sess1", "t1", "u1", "test query")

    assert "short_term" in ctx
    assert "working_summary" in ctx
    assert "relevant_memories" in ctx
    assert len(ctx["short_term"]) == 2
    assert ctx["working_summary"] == "Summary"


@pytest.mark.asyncio
async def test_memory_engine_clear_session():
    """Clearing session removes short-term memory."""
    redis = _make_mock_redis()
    engine = MemoryEngine(redis_client=redis)
    await engine.clear_session("sess1")
    redis.delete.assert_called_once()
