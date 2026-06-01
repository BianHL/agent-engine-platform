"""Backward-compatible HybridRetriever shim.

The retrieval logic has been consolidated into ``RAGPipeline``.  This module
provides a thin wrapper so that existing code and tests importing
``HybridRetriever`` continue to work without changes.

Prefer importing ``RAGPipeline`` from
``app.engines.knowledge_engine.rag_pipeline`` for new code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.engines.knowledge_engine.rag_pipeline import RAGPipeline


class HybridRetriever:
    """Backward-compatible retriever that delegates to ``RAGPipeline``.

    Parameters
    ----------
    vector_store : optional
        Milvus-compatible vector store.
    es_store : optional
        Elasticsearch-compatible fulltext store.
    graph_store : optional
        Neo4j-compatible graph store.
    """

    def __init__(self, vector_store=None, es_store=None, graph_store=None):
        # Deferred import to avoid circular dependency:
        # rag_pipeline -> retriever/__init__ -> retriever -> rag_pipeline
        from app.engines.knowledge_engine.rag_pipeline import RAGPipeline

        self._pipeline = RAGPipeline(
            vector_store=vector_store,
            es_store=es_store,
            graph_store=graph_store,
        )

    # Expose underlying stores for tests that inspect them
    @property
    def vector_store(self):
        return self._pipeline.vector_store

    @property
    def es_store(self):
        return self._pipeline.es_store

    @property
    def graph_store(self):
        return self._pipeline.graph_store

    async def retrieve(
        self,
        query: str,
        query_embedding: list[float],
        knowledge_base_id: str,
        collection_name: str,
        es_index: str,
        dim: int = 1536,
        top_k: int = 5,
        strategy: str = "hybrid",
        graph_enabled: bool = False,
        retrieval_mode: str = "hybrid",
    ) -> list[dict]:
        """Retrieve documents with the specified strategy.

        Delegates to ``RAGPipeline._retrieve_legacy`` for backward
        compatibility.
        """
        return await self._pipeline._retrieve_legacy(
            query=query,
            query_embedding=query_embedding,
            knowledge_base_id=knowledge_base_id,
            collection_name=collection_name,
            es_index=es_index,
            strategy=strategy,
            top_k=top_k,
            graph_enabled=graph_enabled,
            retrieval_mode=retrieval_mode,
            dim=dim,
        )

    @staticmethod
    def _rrf_merge(vector_results, fulltext_results, top_k, k=60):
        """Reciprocal Rank Fusion merge of two result lists."""
        from app.engines.knowledge_engine.rag_pipeline import RAGPipeline

        return RAGPipeline._rrf_merge(vector_results, fulltext_results, top_k, k)

    @staticmethod
    def _enrich_with_citations(results: list[dict]) -> list[dict]:
        """Enrich results with citation metadata."""
        from app.engines.knowledge_engine.rag_pipeline import RAGPipeline

        return RAGPipeline._enrich_with_citations(results)
