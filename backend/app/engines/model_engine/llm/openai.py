import httpx
from typing import AsyncIterator
from app.engines.model_engine.base import BaseLLMAdapter
from app.schemas.common import LLMResponse, TokenUsage, FunctionCallResponse


class OpenAIAdapter(BaseLLMAdapter):
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.api_base = config.get("api_base", "https://api.openai.com/v1")
        self.timeout = config.get("timeout", 30)

    async def chat(self, messages: list[dict], model: str = "gpt-4o", temperature: float = 0.7, max_tokens: int = 4096, **kwargs) -> LLMResponse:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.api_base}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return LLMResponse(
                content=choice["message"]["content"] or "",
                model=model,
                usage=TokenUsage(
                    input_tokens=usage.get("prompt_tokens", 0),
                    output_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0)
                ),
                finish_reason=choice.get("finish_reason", "stop"),
                raw_response=data
            )

    async def chat_stream(self, messages: list[dict], model: str = "gpt-4o", temperature: float = 0.7, max_tokens: int = 4096, **kwargs) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.api_base}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": True}
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line.strip() != "data: [DONE]":
                        import json
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue

    async def function_call(self, messages: list[dict], functions: list[dict], model: str = "gpt-4o", **kwargs) -> FunctionCallResponse:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.api_base}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "messages": messages, "tools": [{"type": "function", "function": f} for f in functions]}
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            msg = choice["message"]
            if msg.get("tool_calls"):
                tc = msg["tool_calls"][0]
                import json
                return FunctionCallResponse(
                    function_name=tc["function"]["name"],
                    arguments=json.loads(tc["function"]["arguments"]),
                    raw_response=data
                )
            return FunctionCallResponse(content=msg.get("content", ""), raw_response=data)
