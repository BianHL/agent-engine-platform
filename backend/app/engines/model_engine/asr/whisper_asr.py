import httpx
from app.engines.model_engine.base import BaseASRAdapter
from app.schemas.common import ASRResult


class WhisperASRAdapter(BaseASRAdapter):
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.api_base = config.get("api_base", "https://api.openai.com/v1")

    async def transcribe(self, audio_data: bytes, model: str = "whisper-1", language: str = "zh", **kwargs) -> ASRResult:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.api_base}/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"file": ("audio.mp3", audio_data, "audio/mpeg")},
                data={"model": model, "language": language}
            )
            resp.raise_for_status()
            data = resp.json()
            return ASRResult(
                text=data.get("text", ""),
                language=language,
                duration=data.get("duration", 0.0),
                confidence=1.0
            )
