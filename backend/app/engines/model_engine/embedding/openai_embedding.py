import httpx
from app.engines.model_engine.base import BaseEmbeddingAdapter


class OpenAIEmbeddingAdapter(BaseEmbeddingAdapter):
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.api_base = config.get("api_base", "https://api.openai.com/v1")

    async def embed(self, texts: list[str], model: str = "text-embedding-3-small", **kwargs) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.api_base}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "input": texts}
            )
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]
