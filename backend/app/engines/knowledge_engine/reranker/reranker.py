from typing import Optional


class Reranker:
    def __init__(self, adapter=None):
        self.adapter = adapter

    async def rerank(
        self,
        query: str,
        documents: list[dict],
        model: str = "rerank-multilingual-v3.0",
        top_k: int = 5,
    ) -> list[dict]:
        if not self.adapter:
            return documents[:top_k]

        texts = [doc.get("content", "") for doc in documents]
        results = await self.adapter.rerank(query, texts, model, top_k)

        reranked = []
        for r in results:
            idx = r.index
            if idx < 0 or idx >= len(documents):
                continue
            doc = documents[idx].copy()
            doc["rerank_score"] = r.score
            reranked.append(doc)

        return reranked[:top_k]
