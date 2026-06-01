"""Unit tests for TTS Adapter - M-011."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.engines.model_engine.tts.tts_adapter import BaseTTSAdapter, OpenAITTSAdapter


@pytest.mark.asyncio
async def test_base_tts_raises():
    """Base TTS adapter raises NotImplementedError."""
    adapter = BaseTTSAdapter()
    with pytest.raises(NotImplementedError):
        await adapter.synthesize("hello")


@pytest.mark.asyncio
async def test_openai_tts_calls_api():
    """OpenAI TTS adapter calls the correct API endpoint."""
    adapter = OpenAITTSAdapter(api_key="test-key")

    mock_response = MagicMock()
    mock_response.content = b"audio-bytes"
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
            post=AsyncMock(return_value=mock_response)
        ))
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

        # The adapter uses httpx.AsyncClient directly
        result = await adapter.synthesize("Hello world", voice="alloy")
        assert result == b"audio-bytes"


def test_openai_tts_init():
    """OpenAI TTS adapter initializes with config."""
    adapter = OpenAITTSAdapter(api_key="sk-test", api_base="https://custom.api.com")
    assert adapter.api_key == "sk-test"
    assert adapter.api_base == "https://custom.api.com"


def test_openai_tts_default_base():
    """OpenAI TTS adapter has default API base."""
    adapter = OpenAITTSAdapter(api_key="sk-test")
    assert adapter.api_base == "https://api.openai.com/v1"
