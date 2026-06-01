import httpx
from typing import AsyncIterator
from app.engines.model_engine.base import BaseLLMAdapter
from app.schemas.common import LLMResponse, TokenUsage


class AnthropicAdapter(BaseLLMAdapter):
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.api_base = config.get("api_base", "https://api.anthropic.com")
        self.timeout = config.get("timeout", 30)

    async def chat(self, messages: list[dict], model: str = "claude-sonnet-4-20250514", temperature: float = 0.7, max_tokens: int = 4096, **kwargs) -> LLMResponse:
        system = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                filtered.append(m)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            body = {"model": model, "messages": filtered, "max_tokens": max_tokens, "temperature": temperature}
            if system:
                body["system"] = system
            resp = await client.post(
                f"{self.api_base}/v1/messages",
                headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                json=body
            )
            resp.raise_for_status()
            data = resp.json()
            content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block["text"]
            usage = data.get("usage", {})
            return LLMResponse(
                content=content,
                model=model,
                usage=TokenUsage(
                    input_tokens=usage.get("input_tokens", 0),
                    output_tokens=usage.get("output_tokens", 0),
                    total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                ),
                finish_reason=data.get("stop_reason", "stop"),
                raw_response=data
            )

    async def chat_stream(self, messages: list[dict], model: str = "claude-sonnet-4-20250514", temperature: float = 0.7, max_tokens: int = 4096, **kwargs) -> AsyncIterator[str]:
        system = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                filtered.append(m)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            body = {"model": model, "messages": filtered, "max_tokens": max_tokens, "temperature": temperature, "stream": True}
            if system:
                body["system"] = system
            async with client.stream(
                "POST",
                f"{self.api_base}/v1/messages",
                headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                json=body
            ) as resp:
                resp.raise_for_status()
                import json
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            event = json.loads(line[6:])
                            if event.get("type") == "content_block_delta":
                                delta = event.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta["text"]
                        except json.JSONDecodeError:
                            continue
