"""TTS adapter implementations."""
import httpx
from typing import Optional


class BaseTTSAdapter:
    """Base TTS adapter interface."""

    async def synthesize(self, text: str, voice: str = "alloy", format: str = "mp3", **kwargs) -> bytes:
        """Convert text to audio bytes."""
        raise NotImplementedError


class OpenAITTSAdapter(BaseTTSAdapter):
    """OpenAI TTS API adapter."""

    def __init__(self, api_key: str, api_base: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.api_base = api_base

    async def synthesize(self, text: str, voice: str = "alloy", format: str = "mp3",
                         model: str = "tts-1", speed: float = 1.0, **kwargs) -> bytes:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.api_base}/audio/speech",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": model,
                    "input": text,
                    "voice": voice,
                    "response_format": format,
                    "speed": speed,
                },
            )
            resp.raise_for_status()
            return resp.content


class EdgeTTSAdapter(BaseTTSAdapter):
    """Microsoft Edge TTS adapter (free, no API key required)."""

    def __init__(self):
        self._rate = "+0%"
        self._volume = "+0%"

    async def synthesize(self, text: str, voice: str = "zh-CN-XiaoxiaoNeural",
                         format: str = "mp3", **kwargs) -> bytes:
        try:
            import edge_tts
            import io

            communicate = edge_tts.Communicate(text, voice, rate=self._rate, volume=self._volume)
            buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])
            return buffer.getvalue()
        except ImportError:
            raise RuntimeError("edge-tts package not installed. Install with: pip install edge-tts")
