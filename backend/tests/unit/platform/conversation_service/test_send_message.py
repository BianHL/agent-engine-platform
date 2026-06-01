"""Unit tests for ConversationService.send_message"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.platform.conversation_service.conversation_service import ConversationService


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


@pytest.fixture
def mock_llm_adapter():
    adapter = MagicMock()
    return adapter


@pytest.fixture
def service(mock_db):
    return ConversationService(db=mock_db)


def _make_chunk(content):
    chunk = MagicMock()
    chunk.content = content
    return chunk


async def _async_gen(items):
    for item in items:
        yield item


@pytest.mark.asyncio
async def test_send_message_yields_error_when_no_adapter(service):
    events = []
    async for event in service.send_message(
        conversation_id="conv-1",
        user_id="user-1",
        content="Hello",
        llm_adapter=None,
    ):
        events.append(event)

    assert len(events) == 1
    assert events[0]["event"] == "error"
    data = json.loads(events[0]["data"])
    assert "No LLM adapter" in data["error"]


@pytest.mark.asyncio
async def test_send_message_saves_user_message(service, mock_db, mock_llm_adapter):
    chunks = [_make_chunk("Hi"), _make_chunk(" there")]
    mock_llm_adapter.chat_stream = MagicMock(return_value=_async_gen(chunks))

    service.add_message = AsyncMock(
        side_effect=[
            {"id": "msg-user-1", "role": "user"},
            {"id": "msg-assistant-1", "role": "assistant"},
        ]
    )
    service._get_context_messages = AsyncMock(return_value=[])

    events = []
    async for event in service.send_message(
        conversation_id="conv-1",
        user_id="user-1",
        content="Hello",
        llm_adapter=mock_llm_adapter,
    ):
        events.append(event)

    assert service.add_message.call_count == 2
    first_call = service.add_message.call_args_list[0]
    assert first_call[0] == ("conv-1", "user", "Hello")


@pytest.mark.asyncio
async def test_send_message_yields_stream_chunks(service, mock_db, mock_llm_adapter):
    chunks = [_make_chunk("Hello"), _make_chunk(" world"), _make_chunk("!")]
    mock_llm_adapter.chat_stream = MagicMock(return_value=_async_gen(chunks))

    service.add_message = AsyncMock(
        side_effect=[
            {"id": "msg-user-1", "role": "user"},
            {"id": "msg-assistant-1", "role": "assistant"},
        ]
    )
    service._get_context_messages = AsyncMock(return_value=[])

    events = []
    async for event in service.send_message(
        conversation_id="conv-1",
        user_id="user-1",
        content="Hi",
        llm_adapter=mock_llm_adapter,
    ):
        events.append(event)

    message_events = [e for e in events if e["event"] == "message"]
    assert len(message_events) == 3
    assert json.loads(message_events[0]["data"])["content"] == "Hello"
    assert json.loads(message_events[1]["data"])["content"] == " world"
    assert json.loads(message_events[2]["data"])["content"] == "!"


@pytest.mark.asyncio
async def test_send_message_yields_done_event(service, mock_db, mock_llm_adapter):
    chunks = [_make_chunk("Response")]
    mock_llm_adapter.chat_stream = MagicMock(return_value=_async_gen(chunks))

    service.add_message = AsyncMock(
        side_effect=[
            {"id": "msg-user-1", "role": "user"},
            {"id": "msg-assistant-1", "role": "assistant"},
        ]
    )
    service._get_context_messages = AsyncMock(return_value=[])

    events = []
    async for event in service.send_message(
        conversation_id="conv-1",
        user_id="user-1",
        content="Hi",
        llm_adapter=mock_llm_adapter,
    ):
        events.append(event)

    done_events = [e for e in events if e["event"] == "done"]
    assert len(done_events) == 1
    data = json.loads(done_events[0]["data"])
    assert data["conversation_id"] == "conv-1"
    assert data["message_id"] == "msg-assistant-1"


@pytest.mark.asyncio
async def test_send_message_passes_params_to_adapter(service, mock_db, mock_llm_adapter):
    mock_llm_adapter.chat_stream = MagicMock(return_value=_async_gen([_make_chunk("ok")]))

    service.add_message = AsyncMock(
        side_effect=[
            {"id": "u1", "role": "user"},
            {"id": "a1", "role": "assistant"},
        ]
    )
    service._get_context_messages = AsyncMock(
        return_value=[{"role": "user", "content": "test"}]
    )

    async for _ in service.send_message(
        conversation_id="conv-1",
        user_id="user-1",
        content="test",
        llm_adapter=mock_llm_adapter,
        model="gpt-4",
        temperature=0.5,
        max_tokens=1000,
        system_prompt="Be helpful",
    ):
        pass

    mock_llm_adapter.chat_stream.assert_called_once_with(
        messages=[
            {"role": "system", "content": "Be helpful"},
            {"role": "user", "content": "test"},
        ],
        model="gpt-4",
        temperature=0.5,
        max_tokens=1000,
    )


@pytest.mark.asyncio
async def test_send_message_includes_context_history(service, mock_db, mock_llm_adapter):
    mock_llm_adapter.chat_stream = MagicMock(return_value=_async_gen([_make_chunk("new")]))

    service.add_message = AsyncMock(
        side_effect=[
            {"id": "u1", "role": "user"},
            {"id": "a1", "role": "assistant"},
        ]
    )
    service._get_context_messages = AsyncMock(
        return_value=[
            {"role": "user", "content": "Old question"},
            {"role": "assistant", "content": "Old answer"},
            {"role": "user", "content": "New question"},
        ]
    )

    async for _ in service.send_message(
        conversation_id="conv-1",
        user_id="user-1",
        content="New question",
        llm_adapter=mock_llm_adapter,
        system_prompt="System",
    ):
        pass

    call_args = mock_llm_adapter.chat_stream.call_args
    messages = call_args[1]["messages"]
    assert messages[0] == {"role": "system", "content": "System"}
    assert messages[1] == {"role": "user", "content": "Old question"}
    assert messages[2] == {"role": "assistant", "content": "Old answer"}
    assert messages[3] == {"role": "user", "content": "New question"}


@pytest.mark.asyncio
async def test_send_message_yields_error_on_adapter_failure(service, mock_db, mock_llm_adapter):
    async def failing_stream(**kwargs):
        raise RuntimeError("LLM service unavailable")
        yield  # noqa: make it an async generator

    mock_llm_adapter.chat_stream = MagicMock(return_value=failing_stream())

    service.add_message = AsyncMock(
        return_value={"id": "u1", "role": "user"}
    )
    service._get_context_messages = AsyncMock(return_value=[])

    events = []
    async for event in service.send_message(
        conversation_id="conv-1",
        user_id="user-1",
        content="Hi",
        llm_adapter=mock_llm_adapter,
    ):
        events.append(event)

    error_events = [e for e in events if e["event"] == "error"]
    assert len(error_events) == 1
    assert "LLM service unavailable" in json.loads(error_events[0]["data"])["error"]


@pytest.mark.asyncio
async def test_send_message_yields_error_on_save_user_message_failure(
    service, mock_db, mock_llm_adapter
):
    service.add_message = AsyncMock(
        side_effect=Exception("DB write failed")
    )

    events = []
    async for event in service.send_message(
        conversation_id="conv-1",
        user_id="user-1",
        content="Hi",
        llm_adapter=mock_llm_adapter,
    ):
        events.append(event)

    assert events[0]["event"] == "error"
    assert "Failed to save user message" in json.loads(events[0]["data"])["error"]


@pytest.mark.asyncio
async def test_send_message_yields_error_on_save_assistant_message_failure(
    service, mock_db, mock_llm_adapter
):
    mock_llm_adapter.chat_stream = MagicMock(return_value=_async_gen([_make_chunk("ok")]))

    service.add_message = AsyncMock(
        side_effect=[
            {"id": "u1", "role": "user"},
            Exception("DB write failed"),
        ]
    )
    service._get_context_messages = AsyncMock(return_value=[])

    events = []
    async for event in service.send_message(
        conversation_id="conv-1",
        user_id="user-1",
        content="Hi",
        llm_adapter=mock_llm_adapter,
    ):
        events.append(event)

    error_events = [e for e in events if e["event"] == "error"]
    assert len(error_events) == 1
    assert "Failed to save assistant message" in json.loads(error_events[0]["data"])["error"]


@pytest.mark.asyncio
async def test_get_context_messages(service, mock_db):
    mock_msg1 = MagicMock()
    mock_msg1.role = "user"
    mock_msg1.content = "First"
    mock_msg2 = MagicMock()
    mock_msg2.role = "assistant"
    mock_msg2.content = "Second"

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_msg2, mock_msg1]
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    messages = await service._get_context_messages("conv-1", limit=20)

    assert messages == [
        {"role": "user", "content": "First"},
        {"role": "assistant", "content": "Second"},
    ]


@pytest.mark.asyncio
async def test_get_context_messages_reverses_order(service, mock_db):
    msgs = []
    for i in range(5):
        m = MagicMock()
        m.role = "user" if i % 2 == 0 else "assistant"
        m.content = f"msg-{i}"
        msgs.append(m)

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = list(reversed(msgs))
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    messages = await service._get_context_messages("conv-1", limit=20)

    assert messages[0]["content"] == "msg-0"
    assert messages[-1]["content"] == "msg-4"


@pytest.mark.asyncio
async def test_send_message_no_system_prompt_when_empty(service, mock_db, mock_llm_adapter):
    mock_llm_adapter.chat_stream = MagicMock(return_value=_async_gen([_make_chunk("ok")]))

    service.add_message = AsyncMock(
        side_effect=[
            {"id": "u1", "role": "user"},
            {"id": "a1", "role": "assistant"},
        ]
    )
    service._get_context_messages = AsyncMock(
        return_value=[{"role": "user", "content": "Hi"}]
    )

    async for _ in service.send_message(
        conversation_id="conv-1",
        user_id="user-1",
        content="Hi",
        llm_adapter=mock_llm_adapter,
        system_prompt="",
    ):
        pass

    call_args = mock_llm_adapter.chat_stream.call_args
    messages = call_args[1]["messages"]
    assert messages[0] == {"role": "user", "content": "Hi"}
    assert len(messages) == 1


@pytest.mark.asyncio
async def test_send_message_chunk_without_content_attr(service, mock_db, mock_llm_adapter):
    class PlainChunk:
        def __init__(self, text):
            self._text = text

        def __str__(self):
            return self._text

    mock_llm_adapter.chat_stream = MagicMock(
        return_value=_async_gen([PlainChunk("plain text")])
    )

    service.add_message = AsyncMock(
        side_effect=[
            {"id": "u1", "role": "user"},
            {"id": "a1", "role": "assistant"},
        ]
    )
    service._get_context_messages = AsyncMock(return_value=[])

    events = []
    async for event in service.send_message(
        conversation_id="conv-1",
        user_id="user-1",
        content="Hi",
        llm_adapter=mock_llm_adapter,
    ):
        events.append(event)

    message_events = [e for e in events if e["event"] == "message"]
    assert len(message_events) == 1
    assert json.loads(message_events[0]["data"])["content"] == "plain text"
