"""
Integration tests for model engine adapters (M-001 ~ M-024).

All tests mock at the httpx level (not at the adapter level) to verify
that adapters construct correct request payloads and parse responses properly.
"""
import asyncio
import json
import time
from contextlib import asynccontextmanager
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.exceptions import AllProvidersUnavailableError
from app.engines.model_engine.asr.whisper_asr import WhisperASRAdapter
from app.engines.model_engine.cost_tracker import CostTracker
from app.engines.model_engine.embedding.openai_embedding import OpenAIEmbeddingAdapter
from app.engines.model_engine.llm.anthropic import AnthropicAdapter
from app.engines.model_engine.llm.custom_openai import CustomOpenAIAdapter
from app.engines.model_engine.llm.ollama import OllamaAdapter
from app.engines.model_engine.llm.openai import OpenAIAdapter
from app.engines.model_engine.rerank.cohere_rerank import CohereRerankAdapter
from app.engines.model_engine.router import CircuitBreaker, ModelRouter
from app.models.base import Base, ModelConfigModel, UsageLogModel
from app.schemas.common import ProviderEndpoint

# ---------------------------------------------------------------------------
# Helper: build a mock httpx.Response
# ---------------------------------------------------------------------------


def _mock_response(status_code: int = 200, json_data: dict | None = None, text: str = "") -> MagicMock:
    """Create a mock httpx.Response with the given status and body."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text or json.dumps(json_data or {})
    resp.json.return_value = json_data or {}
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


def _make_stream_response(lines: list[str], status_code: int = 200) -> MagicMock:
    """Create a mock response whose aiter_lines() yields the given lines."""
    resp = _mock_response(status_code=status_code)

    async def _aiter_lines():
        for line in lines:
            yield line

    resp.aiter_lines = _aiter_lines
    return resp


@asynccontextmanager
async def _stream_cm(response):
    """Async context manager that yields a mock stream response."""
    yield response


# =========================================================================
# M-001: OpenAI adapter -- chat()
# =========================================================================


class TestOpenAIChat:
    """M-001: Verify OpenAI chat sends correct payload and parses response."""

    @pytest.mark.asyncio
    async def test_chat_sends_correct_payload(self):
        adapter = OpenAIAdapter(config={"api_key": "sk-test", "api_base": "https://api.openai.com/v1", "timeout": 10})
        messages = [{"role": "user", "content": "Hello"}]
        resp_data = {
            "choices": [{"message": {"content": "Hi there!"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "model": "gpt-4o",
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=_mock_response(200, resp_data))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.llm.openai.httpx.AsyncClient", return_value=mock_client):
            result = await adapter.chat(messages, model="gpt-4o", temperature=0.5, max_tokens=100)

        # Verify request
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/chat/completions" in call_args[0][0]
        body = call_args[1]["json"]
        assert body["model"] == "gpt-4o"
        assert body["messages"] == messages
        assert body["temperature"] == 0.5
        assert body["max_tokens"] == 100
        assert call_args[1]["headers"]["Authorization"] == "Bearer sk-test"

        # Verify response parsing
        assert result.content == "Hi there!"
        assert result.model == "gpt-4o"
        assert result.usage.input_tokens == 10
        assert result.usage.output_tokens == 5
        assert result.finish_reason == "stop"


# =========================================================================
# M-002: OpenAI adapter -- chat_stream()
# =========================================================================


class TestOpenAIStream:
    """M-002: Verify OpenAI streaming chat yields content deltas."""

    @pytest.mark.asyncio
    async def test_stream_yields_content_deltas(self):
        adapter = OpenAIAdapter(config={"api_key": "sk-test", "api_base": "https://api.openai.com/v1", "timeout": 10})
        messages = [{"role": "user", "content": "Hello"}]

        sse_lines = [
            'data: {"choices":[{"delta":{"content":"Hello"},"index":0}]}',
            'data: {"choices":[{"delta":{"content":" world"},"index":0}]}',
            "data: [DONE]",
        ]
        stream_resp = _make_stream_response(sse_lines)

        mock_client = AsyncMock()
        mock_client.stream = MagicMock(return_value=_stream_cm(stream_resp))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.llm.openai.httpx.AsyncClient", return_value=mock_client):
            chunks = []
            async for chunk in adapter.chat_stream(messages, model="gpt-4o"):
                chunks.append(chunk)

        assert chunks == ["Hello", " world"]

        # Verify stream=True in payload
        call_args = mock_client.stream.call_args
        body = call_args[1]["json"] if "json" in call_args[1] else call_args[2].get("json", {})
        assert body.get("stream") is True


# =========================================================================
# M-003: OpenAI adapter -- function_call()
# =========================================================================


class TestOpenAIFunctionCall:
    """M-003: Verify OpenAI function_call sends tools and parses tool_calls."""

    @pytest.mark.asyncio
    async def test_function_call_with_tool_calls(self):
        adapter = OpenAIAdapter(config={"api_key": "sk-test", "api_base": "https://api.openai.com/v1", "timeout": 10})
        messages = [{"role": "user", "content": "What's the weather?"}]
        functions = [{"name": "get_weather", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}}}]

        resp_data = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"city": "Beijing"}',
                        }
                    }]
                }
            }],
            "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=_mock_response(200, resp_data))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.llm.openai.httpx.AsyncClient", return_value=mock_client):
            result = await adapter.function_call(messages, functions, model="gpt-4o")

        # Verify tools format in request
        body = mock_client.post.call_args[1]["json"]
        assert "tools" in body
        assert body["tools"][0]["type"] == "function"
        assert body["tools"][0]["function"]["name"] == "get_weather"

        # Verify parsed result
        assert result.function_name == "get_weather"
        assert result.arguments == {"city": "Beijing"}


# =========================================================================
# M-004: Anthropic adapter -- chat()
# =========================================================================


class TestAnthropicChat:
    """M-004: Verify Anthropic chat extracts system message and sends correct payload."""

    @pytest.mark.asyncio
    async def test_chat_extracts_system_and_sends_correct_payload(self):
        adapter = AnthropicAdapter(config={"api_key": "sk-ant-test", "api_base": "https://api.anthropic.com", "timeout": 10})
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
        ]
        resp_data = {
            "content": [{"type": "text", "text": "Hi!"}],
            "usage": {"input_tokens": 15, "output_tokens": 8},
            "stop_reason": "end_turn",
            "model": "claude-sonnet-4-20250514",
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=_mock_response(200, resp_data))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.llm.anthropic.httpx.AsyncClient", return_value=mock_client):
            result = await adapter.chat(messages, model="claude-sonnet-4-20250514", temperature=0.3, max_tokens=200)

        # Verify request payload
        call_args = mock_client.post.call_args
        body = call_args[1]["json"]
        assert body["model"] == "claude-sonnet-4-20250514"
        assert body["system"] == "You are a helpful assistant."
        # System message should be filtered from messages list
        assert all(m["role"] != "system" for m in body["messages"])
        assert body["temperature"] == 0.3
        assert body["max_tokens"] == 200

        # Verify headers
        headers = call_args[1]["headers"]
        assert headers["x-api-key"] == "sk-ant-test"
        assert headers["anthropic-version"] == "2023-06-01"

        # Verify URL
        assert "/v1/messages" in call_args[0][0]

        # Verify response parsing
        assert result.content == "Hi!"
        assert result.usage.input_tokens == 15
        assert result.usage.output_tokens == 8
        assert result.finish_reason == "end_turn"


# =========================================================================
# M-005: Anthropic adapter -- chat_stream()
# =========================================================================


class TestAnthropicStream:
    """M-005: Verify Anthropic streaming chat yields text deltas."""

    @pytest.mark.asyncio
    async def test_stream_yields_text_deltas(self):
        adapter = AnthropicAdapter(config={"api_key": "sk-ant-test", "api_base": "https://api.anthropic.com", "timeout": 10})
        messages = [{"role": "user", "content": "Hello"}]

        sse_lines = [
            'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello"}}',
            'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":" world"}}',
            'data: {"type":"message_stop"}',
        ]
        stream_resp = _make_stream_response(sse_lines)

        mock_client = AsyncMock()
        mock_client.stream = MagicMock(return_value=_stream_cm(stream_resp))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.llm.anthropic.httpx.AsyncClient", return_value=mock_client):
            chunks = []
            async for chunk in adapter.chat_stream(messages):
                chunks.append(chunk)

        assert chunks == ["Hello", " world"]


# =========================================================================
# M-006: DeepSeek adapter (CustomOpenAI) -- chat()
# =========================================================================


class TestDeepSeekAdapter:
    """M-006: Verify DeepSeek adapter (CustomOpenAI subclass) uses OpenAI-compatible format."""

    @pytest.mark.asyncio
    async def test_deepseek_chat_uses_openai_format(self):
        adapter = CustomOpenAIAdapter(config={"api_key": "ds-key", "api_base": "https://api.deepseek.com/v1", "timeout": 15})
        messages = [{"role": "user", "content": "Explain recursion"}]
        resp_data = {
            "choices": [{"message": {"content": "Recursion is..."}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 50, "total_tokens": 62},
            "model": "deepseek-chat",
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=_mock_response(200, resp_data))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.llm.openai.httpx.AsyncClient", return_value=mock_client):
            result = await adapter.chat(messages, model="deepseek-chat")

        call_args = mock_client.post.call_args
        assert "deepseek.com" in call_args[0][0]
        assert call_args[1]["headers"]["Authorization"] == "Bearer ds-key"
        assert result.content == "Recursion is..."


# =========================================================================
# M-007: Ollama adapter -- chat() and chat_stream()
# =========================================================================


class TestOllamaAdapter:
    """M-007: Verify Ollama adapter uses /api/chat endpoint with Ollama-specific format."""

    @pytest.mark.asyncio
    async def test_chat_uses_ollama_endpoint_and_format(self):
        adapter = OllamaAdapter(config={"api_base": "http://localhost:11434", "timeout": 60})
        messages = [{"role": "user", "content": "Hi"}]
        resp_data = {
            "message": {"content": "Hello!"},
            "done": True,
            "prompt_eval_count": 20,
            "eval_count": 10,
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=_mock_response(200, resp_data))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.llm.ollama.httpx.AsyncClient", return_value=mock_client):
            result = await adapter.chat(messages, model="qwen2.5", temperature=0.8, max_tokens=500)

        # Verify request
        call_args = mock_client.post.call_args
        assert "/api/chat" in call_args[0][0]
        body = call_args[1]["json"]
        assert body["model"] == "qwen2.5"
        assert body["stream"] is False
        assert body["options"]["temperature"] == 0.8
        assert body["options"]["num_predict"] == 500

        # Verify response parsing
        assert result.content == "Hello!"
        assert result.usage.input_tokens == 20
        assert result.usage.output_tokens == 10
        assert result.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_stream_yields_ndjson_chunks(self):
        adapter = OllamaAdapter(config={"api_base": "http://localhost:11434", "timeout": 60})
        messages = [{"role": "user", "content": "Hi"}]

        ndjson_lines = [
            '{"message":{"content":"Hello"},"done":false}',
            '{"message":{"content":" world"},"done":false}',
            '{"message":{"content":""},"done":true}',
        ]
        stream_resp = _make_stream_response(ndjson_lines)

        mock_client = AsyncMock()
        mock_client.stream = MagicMock(return_value=_stream_cm(stream_resp))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.llm.ollama.httpx.AsyncClient", return_value=mock_client):
            chunks = []
            async for chunk in adapter.chat_stream(messages, model="qwen2.5"):
                chunks.append(chunk)

        assert chunks == ["Hello", " world"]


# =========================================================================
# M-008: Embedding adapter -- produces correct dimension vectors
# =========================================================================


class TestEmbeddingAdapter:
    """M-008: Verify embedding adapter returns vectors with expected dimensions."""

    @pytest.mark.asyncio
    async def test_embed_returns_correct_dimensions(self):
        adapter = OpenAIEmbeddingAdapter(config={"api_key": "sk-test", "api_base": "https://api.openai.com/v1"})
        texts = ["hello world", "test text"]

        # 1536-dim vectors (text-embedding-3-small default)
        vec_a = [0.1] * 1536
        vec_b = [0.2] * 1536
        resp_data = {
            "data": [
                {"embedding": vec_a, "index": 0},
                {"embedding": vec_b, "index": 1},
            ],
            "model": "text-embedding-3-small",
            "usage": {"prompt_tokens": 8, "total_tokens": 8},
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=_mock_response(200, resp_data))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.embedding.openai_embedding.httpx.AsyncClient", return_value=mock_client):
            embeddings = await adapter.embed(texts, model="text-embedding-3-small")

        # Verify request
        body = mock_client.post.call_args[1]["json"]
        assert body["input"] == texts
        assert body["model"] == "text-embedding-3-small"
        assert "/embeddings" in mock_client.post.call_args[0][0]

        # Verify dimensions
        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1536
        assert len(embeddings[1]) == 1536
        assert embeddings[0][0] == 0.1
        assert embeddings[1][0] == 0.2


# =========================================================================
# M-009: Rerank adapter -- returns sorted results
# =========================================================================


class TestRerankAdapter:
    """M-009: Verify rerank adapter returns results sorted by relevance score."""

    @pytest.mark.asyncio
    async def test_rerank_returns_sorted_results(self):
        adapter = CohereRerankAdapter(config={"api_key": "cohere-key", "api_base": "https://api.cohere.com"})
        query = "What is Python?"
        documents = ["Python is a programming language", "The weather is nice", "Python was created by Guido"]

        resp_data = {
            "results": [
                {"index": 0, "relevance_score": 0.95},
                {"index": 2, "relevance_score": 0.80},
                {"index": 1, "relevance_score": 0.15},
            ]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=_mock_response(200, resp_data))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.rerank.cohere_rerank.httpx.AsyncClient", return_value=mock_client):
            results = await adapter.rerank(query, documents, model="rerank-multilingual-v3.0", top_k=3)

        # Verify request
        body = mock_client.post.call_args[1]["json"]
        assert body["query"] == query
        assert body["documents"] == documents
        assert body["top_n"] == 3
        assert "/v1/rerank" in mock_client.post.call_args[0][0]

        # Verify results are returned in API order (already sorted by score)
        assert len(results) == 3
        assert results[0].score >= results[1].score >= results[2].score
        assert results[0].document == "Python is a programming language"
        assert results[1].document == "Python was created by Guido"
        assert results[2].document == "The weather is nice"

    @pytest.mark.asyncio
    async def test_rerank_respects_top_k(self):
        adapter = CohereRerankAdapter(config={"api_key": "cohere-key", "api_base": "https://api.cohere.com"})
        resp_data = {
            "results": [
                {"index": 0, "relevance_score": 0.95},
            ]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=_mock_response(200, resp_data))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.rerank.cohere_rerank.httpx.AsyncClient", return_value=mock_client):
            results = await adapter.rerank("query", ["doc1", "doc2"], top_k=1)

        body = mock_client.post.call_args[1]["json"]
        assert body["top_n"] == 1
        assert len(results) == 1


# =========================================================================
# M-010: ASR adapter -- sends correct multipart form
# =========================================================================


class TestASRAdapter:
    """M-010: Verify ASR adapter sends audio as multipart form data."""

    @pytest.mark.asyncio
    async def test_transcribe_sends_multipart_form(self):
        adapter = WhisperASRAdapter(config={"api_key": "sk-test", "api_base": "https://api.openai.com/v1"})
        audio_data = b"\xff\xfb\x90\x00" * 100  # Fake MP3 data

        resp_data = {
            "text": "Hello, this is a transcription.",
            "duration": 5.2,
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=_mock_response(200, resp_data))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.asr.whisper_asr.httpx.AsyncClient", return_value=mock_client):
            result = await adapter.transcribe(audio_data, model="whisper-1", language="zh")

        # Verify request was made
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args

        # Verify URL
        assert "/audio/transcriptions" in call_args[0][0]

        # Verify headers
        assert call_args[1]["headers"]["Authorization"] == "Bearer sk-test"

        # Verify multipart: files parameter should contain the audio
        assert "files" in call_args[1]
        files = call_args[1]["files"]
        assert "file" in files
        file_tuple = files["file"]
        assert file_tuple[0] == "audio.mp3"  # filename
        assert file_tuple[1] == audio_data  # content
        assert file_tuple[2] == "audio/mpeg"  # content type

        # Verify form data fields
        assert "data" in call_args[1]
        data = call_args[1]["data"]
        assert data["model"] == "whisper-1"
        assert data["language"] == "zh"

        # Verify response parsing
        assert result.text == "Hello, this is a transcription."
        assert result.language == "zh"
        assert result.duration == 5.2


# =========================================================================
# M-012: Timeout handling -- raises after configured seconds
# =========================================================================


class TestTimeoutHandling:
    """M-012: Verify that timeout is respected and raises on delay."""

    @pytest.mark.asyncio
    async def test_timeout_raises_on_slow_response(self):
        adapter = OpenAIAdapter(config={"api_key": "sk-test", "api_base": "https://api.openai.com/v1", "timeout": 1})

        async def _slow_post(*args, **kwargs):
            await asyncio.sleep(5)
            return _mock_response(200, {})

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Connection timed out"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.llm.openai.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(httpx.TimeoutException):
                await adapter.chat([{"role": "user", "content": "Hi"}])

    @pytest.mark.asyncio
    async def test_timeout_value_passed_to_client(self):
        adapter = OpenAIAdapter(config={"api_key": "sk-test", "api_base": "https://api.openai.com/v1", "timeout": 42})

        resp_data = {
            "choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=_mock_response(200, resp_data))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.llm.openai.httpx.AsyncClient", return_value=mock_client) as mock_cls:
            await adapter.chat([{"role": "user", "content": "Hi"}])
            # Verify timeout was passed to the AsyncClient constructor
            call_kwargs = mock_cls.call_args
            assert call_kwargs[1].get("timeout") == 42


# =========================================================================
# M-013: Retry on transient errors
# =========================================================================


class TestRetryOnTransientErrors:
    """M-013: Verify adapter behavior when first call returns 500, then succeeds."""

    @pytest.mark.asyncio
    async def test_first_call_fails_second_succeeds(self):
        adapter = OpenAIAdapter(config={"api_key": "sk-test", "api_base": "https://api.openai.com/v1", "timeout": 10})

        success_data = {
            "choices": [{"message": {"content": "OK"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
        }

        # First call: 500, second call: 200
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[
                _mock_response(500, {"error": "Internal Server Error"}),
                _mock_response(200, success_data),
            ]
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.llm.openai.httpx.AsyncClient", return_value=mock_client):
            # First call should raise
            with pytest.raises(httpx.HTTPStatusError):
                await adapter.chat([{"role": "user", "content": "Hi"}])

            # Second call should succeed (retry simulation)
            result = await adapter.chat([{"role": "user", "content": "Hi"}])
            assert result.content == "OK"

        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit_then_success(self):
        adapter = AnthropicAdapter(config={"api_key": "sk-ant", "api_base": "https://api.anthropic.com", "timeout": 10})

        success_data = {
            "content": [{"type": "text", "text": "Done"}],
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "stop_reason": "end_turn",
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[
                _mock_response(429, {"error": "rate_limited"}),
                _mock_response(200, success_data),
            ]
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.engines.model_engine.llm.anthropic.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(httpx.HTTPStatusError):
                await adapter.chat([{"role": "user", "content": "Hi"}])

            result = await adapter.chat([{"role": "user", "content": "Hi"}])
            assert result.content == "Done"

        assert mock_client.post.call_count == 2


# =========================================================================
# M-015: Weighted routing distributes according to weights
# =========================================================================


class TestWeightedRouting:
    """M-015: Verify weighted selection distributes traffic proportionally."""

    @pytest.mark.asyncio
    async def test_weighted_routing_respects_weights(self):
        router = ModelRouter()

        # Two endpoints: one with weight 9, one with weight 1
        ep_a = ProviderEndpoint(provider_id="a", model_name="gpt-4o", weight=9)
        ep_b = ProviderEndpoint(provider_id="b", model_name="gpt-4o", weight=1)
        router.register_endpoint("gpt-4o", ep_a)
        router.register_endpoint("gpt-4o", ep_b)

        # Run 1000 selections
        counts = {"a": 0, "b": 0}
        for _ in range(1000):
            ep = await router._weighted_select("gpt-4o")
            counts[ep.provider_id] += 1

        # With weight 9:1, expect ~90% vs ~10% (allow 15% tolerance)
        assert counts["a"] > 750, f"Expected ~900 for a, got {counts['a']}"
        assert counts["b"] < 250, f"Expected ~100 for b, got {counts['b']}"

    @pytest.mark.asyncio
    async def test_weighted_routing_single_endpoint(self):
        router = ModelRouter()
        ep = ProviderEndpoint(provider_id="solo", model_name="gpt-4o", weight=5)
        router.register_endpoint("gpt-4o", ep)

        for _ in range(10):
            selected = await router._weighted_select("gpt-4o")
            assert selected.provider_id == "solo"


# =========================================================================
# M-016: Health endpoint filtering
# =========================================================================


class TestHealthFiltering:
    """M-016: Verify unhealthy endpoints are excluded from routing."""

    @pytest.mark.asyncio
    async def test_unhealthy_endpoint_excluded(self):
        router = ModelRouter()
        ep_healthy = ProviderEndpoint(provider_id="h1", model_name="gpt-4o", healthy=True)
        ep_unhealthy = ProviderEndpoint(provider_id="u1", model_name="gpt-4o", healthy=False)
        router.register_endpoint("gpt-4o", ep_healthy)
        router.register_endpoint("gpt-4o", ep_unhealthy)

        # All selections should return the healthy endpoint
        for _ in range(20):
            selected = await router.select_provider("gpt-4o", strategy="round_robin")
            assert selected.provider_id == "h1"

    @pytest.mark.asyncio
    async def test_circuit_breaker_filters_endpoint(self):
        router = ModelRouter()
        ep_a = ProviderEndpoint(provider_id="a", model_name="gpt-4o", healthy=True)
        ep_b = ProviderEndpoint(provider_id="b", model_name="gpt-4o", healthy=True)
        router.register_endpoint("gpt-4o", ep_a)
        router.register_endpoint("gpt-4o", ep_b)

        # Trip the circuit breaker for endpoint "a"
        for _ in range(5):
            await router.record_failure("gpt-4o", "a")

        # Now only "b" should be available
        for _ in range(20):
            selected = await router.select_provider("gpt-4o", strategy="round_robin")
            assert selected.provider_id == "b"


# =========================================================================
# M-017: All unavailable fallback
# =========================================================================


class TestAllUnavailable:
    """M-017: Verify AllProvidersUnavailableError when all endpoints are down."""

    @pytest.mark.asyncio
    async def test_all_endpoints_unhealthy_raises(self):
        router = ModelRouter()
        ep1 = ProviderEndpoint(provider_id="p1", model_name="gpt-4o", healthy=False)
        ep2 = ProviderEndpoint(provider_id="p2", model_name="gpt-4o", healthy=False)
        router.register_endpoint("gpt-4o", ep1)
        router.register_endpoint("gpt-4o", ep2)

        with pytest.raises(AllProvidersUnavailableError):
            await router.select_provider("gpt-4o")

    @pytest.mark.asyncio
    async def test_all_circuit_breakers_open_raises(self):
        router = ModelRouter()
        ep1 = ProviderEndpoint(provider_id="p1", model_name="gpt-4o", healthy=True)
        ep2 = ProviderEndpoint(provider_id="p2", model_name="gpt-4o", healthy=True)
        router.register_endpoint("gpt-4o", ep1)
        router.register_endpoint("gpt-4o", ep2)

        # Trip both circuit breakers
        for _ in range(5):
            await router.record_failure("gpt-4o", "p1")
            await router.record_failure("gpt-4o", "p2")

        with pytest.raises(AllProvidersUnavailableError):
            await router.select_provider("gpt-4o")

    @pytest.mark.asyncio
    async def test_no_endpoints_registered_raises(self):
        router = ModelRouter()
        with pytest.raises(AllProvidersUnavailableError):
            await router.select_provider("nonexistent-model")


# =========================================================================
# M-018: Primary-backup fallback
# =========================================================================


class TestPrimaryBackupFallback:
    """M-018: Verify fallback activates when primary circuit breaker is open."""

    @pytest.mark.asyncio
    async def test_fallback_to_backup_on_circuit_breaker_open(self):
        router = ModelRouter()
        primary = ProviderEndpoint(provider_id="primary", model_name="gpt-4o", healthy=True)
        backup = ProviderEndpoint(provider_id="backup", model_name="gpt-4o", healthy=True)
        router.register_endpoint("gpt-4o", primary)
        router.register_endpoint("gpt-4o", backup)

        # Trip primary circuit breaker
        for _ in range(5):
            await router.record_failure("gpt-4o", "primary")

        # Verify primary is unavailable
        cb_key = "gpt-4o:primary"
        assert router._circuit_breakers[cb_key].state == "open"
        assert not await router._circuit_breakers[cb_key].is_available()

        # Backup should be selected
        for _ in range(10):
            selected = await router.select_provider("gpt-4o")
            assert selected.provider_id == "backup"

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovers_after_timeout(self):
        router = ModelRouter()
        primary = ProviderEndpoint(provider_id="primary", model_name="gpt-4o", healthy=True)
        backup = ProviderEndpoint(provider_id="backup", model_name="gpt-4o", healthy=True)
        router.register_endpoint("gpt-4o", primary)
        router.register_endpoint("gpt-4o", backup)

        # Trip primary with a short recovery timeout
        cb = router._circuit_breakers["gpt-4o:primary"]
        cb.recovery_timeout = 0.1  # 100ms

        for _ in range(5):
            await router.record_failure("gpt-4o", "primary")
        assert cb.state == "open"

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Primary should now be available again (half-open -> closed on success)
        assert await cb.is_available()
        await router.record_success("gpt-4o", "primary")
        assert cb.state == "closed"


# =========================================================================
# M-021: Cost calculation
# =========================================================================


class TestCostCalculation:
    """M-021: Verify cost is calculated correctly based on token counts and pricing."""

    @pytest.mark.asyncio
    async def test_cost_calculated_from_token_pricing(self, db_session: AsyncSession):
        # Insert a model config with known pricing: $0.01 / 1K input, $0.03 / 1K output
        config = ModelConfigModel(
            tenant_id="t1",
            provider_id="p1",
            model_name="gpt-4o",
            model_type="llm",
            config={"input_price": 0.01, "output_price": 0.03},
        )
        db_session.add(config)
        await db_session.flush()

        tracker = CostTracker(db_session)
        cost = await tracker.track(
            tenant_id="t1",
            user_id="u1",
            provider="openai",
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
        )

        # Expected: (1000 * 0.01 + 500 * 0.03) / 1000 = (10 + 15) / 1000 = 0.025
        assert abs(cost - 0.025) < 1e-9

    @pytest.mark.asyncio
    async def test_cost_zero_when_no_pricing_config(self, db_session: AsyncSession):
        tracker = CostTracker(db_session)
        cost = await tracker.track(
            tenant_id="t1",
            user_id="u1",
            provider="openai",
            model="unknown-model",
            input_tokens=1000,
            output_tokens=1000,
        )
        assert cost == 0.0


# =========================================================================
# M-022: Budget alerts
# =========================================================================


class TestBudgetAlerts:
    """M-022: Verify budget alert detection from usage data."""

    @pytest.mark.asyncio
    async def test_usage_exceeds_budget_threshold(self, db_session: AsyncSession):
        # Insert usage logs that sum to a high cost
        for i in range(5):
            log = UsageLogModel(
                tenant_id="t1",
                user_id="u1",
                model_provider="openai",
                model_name="gpt-4o",
                input_tokens=10000,
                output_tokens=5000,
                cost=0.25,
                request_type="chat",
            )
            db_session.add(log)
        await db_session.flush()

        tracker = CostTracker(db_session)
        usage = await tracker.get_usage("t1")

        budget_limit = 1.0
        assert usage["total_cost"] > budget_limit  # 5 * 0.25 = 1.25 > 1.0
        assert usage["request_count"] == 5

    @pytest.mark.asyncio
    async def test_usage_within_budget(self, db_session: AsyncSession):
        log = UsageLogModel(
            tenant_id="t2",
            user_id="u1",
            model_provider="openai",
            model_name="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            cost=0.001,
            request_type="chat",
        )
        db_session.add(log)
        await db_session.flush()

        tracker = CostTracker(db_session)
        usage = await tracker.get_usage("t2")

        budget_limit = 1.0
        assert usage["total_cost"] < budget_limit


# =========================================================================
# M-023: Usage reports -- aggregation with date filters
# =========================================================================


class TestUsageReports:
    """M-023: Verify usage aggregation with date range filters."""

    @pytest.mark.asyncio
    async def test_usage_aggregation_returns_correct_totals(self, db_session: AsyncSession):
        # Insert multiple usage logs
        for i in range(3):
            log = UsageLogModel(
                tenant_id="t_report",
                user_id="u1",
                model_provider="openai",
                model_name="gpt-4o",
                input_tokens=100,
                output_tokens=50,
                cost=0.01,
                request_type="chat",
            )
            db_session.add(log)
        await db_session.flush()

        tracker = CostTracker(db_session)
        usage = await tracker.get_usage("t_report")

        assert usage["total_input_tokens"] == 300
        assert usage["total_output_tokens"] == 150
        assert abs(float(usage["total_cost"]) - 0.03) < 1e-9
        assert usage["request_count"] == 3

    @pytest.mark.asyncio
    async def test_usage_filtered_by_tenant(self, db_session: AsyncSession):
        # Insert logs for two different tenants
        for tid in ["t_a", "t_b"]:
            log = UsageLogModel(
                tenant_id=tid,
                user_id="u1",
                model_provider="openai",
                model_name="gpt-4o",
                input_tokens=100,
                output_tokens=50,
                cost=0.05,
                request_type="chat",
            )
            db_session.add(log)
        await db_session.flush()

        tracker = CostTracker(db_session)
        usage_a = await tracker.get_usage("t_a")
        usage_b = await tracker.get_usage("t_b")

        assert usage_a["request_count"] == 1
        assert usage_b["request_count"] == 1
        assert abs(float(usage_a["total_cost"]) - 0.05) < 1e-9


# =========================================================================
# M-024: Usage reports -- per-model breakdown
# =========================================================================


class TestUsagePerModel:
    """M-024: Verify per-model usage breakdown via direct DB queries."""

    @pytest.mark.asyncio
    async def test_per_model_usage_breakdown(self, db_session: AsyncSession):
        # Insert logs for different models
        models = [
            ("openai", "gpt-4o", 0.05),
            ("openai", "gpt-4o", 0.05),
            ("anthropic", "claude-sonnet-4-20250514", 0.08),
        ]
        for provider, model, cost in models:
            log = UsageLogModel(
                tenant_id="t_breakdown",
                user_id="u1",
                model_provider=provider,
                model_name=model,
                input_tokens=100,
                output_tokens=50,
                cost=cost,
                request_type="chat",
            )
            db_session.add(log)
        await db_session.flush()

        # Query per-model breakdown
        from sqlalchemy import func
        stmt = (
            select(
                UsageLogModel.model_name,
                func.sum(UsageLogModel.cost).label("total_cost"),
                func.count(UsageLogModel.id).label("count"),
            )
            .where(UsageLogModel.tenant_id == "t_breakdown")
            .group_by(UsageLogModel.model_name)
        )
        result = await db_session.execute(stmt)
        rows = {row.model_name: row for row in result.all()}

        assert "gpt-4o" in rows
        assert "claude-sonnet-4-20250514" in rows
        assert rows["gpt-4o"].count == 2
        assert abs(float(rows["gpt-4o"].total_cost) - 0.10) < 1e-9
        assert rows["claude-sonnet-4-20250514"].count == 1
        assert abs(float(rows["claude-sonnet-4-20250514"].total_cost) - 0.08) < 1e-9
