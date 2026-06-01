import httpx
from app.engines.model_engine.base import BaseRerankAdapter
from app.schemas.common import RerankResult


class CohereRerankAdapter(BaseRerankAdapter):
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.api_base = config.get("api_base", "https://api.cohere.com")

    async def rerank(self, query: str, documents: list[str], model: str = "rerank-multilingual-v3.0", top_k: int = 10, **kwargs) -> list[RerankResult]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.api_base}/v1/rerank",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "query": query, "documents": documents, "top_n": top_k}
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("results", []):
                results.append(RerankResult(
                    document=documents[item["index"]],
                    score=item["relevance_score"],
                    index=item["index"]
                ))
            return results
