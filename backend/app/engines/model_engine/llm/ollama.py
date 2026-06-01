import httpx
from typing import AsyncIterator
from app.engines.model_engine.base import BaseLLMAdapter
from app.schemas.common import LLMResponse, TokenUsage


class OllamaAdapter(BaseLLMAdapter):
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_base = config.get("api_base", "http://localhost:11434")
        self.timeout = config.get("timeout", 120)

    async def chat(self, messages: list[dict], model: str = "qwen2.5", temperature: float = 0.7, max_tokens: int = 4096, **kwargs) -> LLMResponse:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.api_base}/api/chat",
                json={"model": model, "messages": messages, "stream": False, "options": {"temperature": temperature, "num_predict": max_tokens}}
            )
            resp.raise_for_status()
            data = resp.json()
            msg = data.get("message", {})
            return LLMResponse(
                content=msg.get("content", ""),
                model=model,
                usage=TokenUsage(
                    input_tokens=data.get("prompt_eval_count", 0),
                    output_tokens=data.get("eval_count", 0),
                    total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                ),
                finish_reason="stop" if data.get("done") else "length",
                raw_response=data
            )

    async def chat_stream(self, messages: list[dict], model: str = "qwen2.5", temperature: float = 0.7, max_tokens: int = 4096, **kwargs) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.api_base}/api/chat",
                json={"model": model, "messages": messages, "stream": True, "options": {"temperature": temperature, "num_predict": max_tokens}}
            ) as resp:
                resp.raise_for_status()
                import json
                async for line in resp.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
