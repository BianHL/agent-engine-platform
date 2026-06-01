"""End-to-end RAG pipeline: query -> retrieve -> rerank -> generate.

Supports four LightRAG retrieval modes:
- naive:  plain vector similarity
- local:  entity-focused graph + vector retrieval
- global: theme-focused graph retrieval
- hybrid: combine local + global with weighted RRF fusion

Legacy strategies (vector / fulltext / hybrid / graph_rag) are also supported
via the ``strategy`` parameter.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.engines.knowledge_engine.retriever.dual_retriever import (
    DualLevelRetriever,
    RetrievalMode,
)
from app.engines.knowledge_engine.retriever.graph_retriever import GraphRetriever
from app.engines.knowledge_engine.reranker.reranker import Reranker

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Complete RAG pipeline integrating retrieval, reranking, and generation.

    Consolidates all retrieval strategies (vector, fulltext, hybrid, graph_rag,
    and LightRAG local/global/hybrid) into a single class.  ``DualLevelRetriever``
    handles the LightRAG dual-level keyword extraction and graph search, while
    legacy strategies (vector / fulltext / hybrid / graph_rag) are implemented
    directly here.

    Parameters
    ----------
    vector_store : optional
        Milvus-compatible vector store.
    es_store : optional
        Elasticsearch-compatible fulltext store.
    graph_store : optional
        Neo4j-compatible graph store.
    embedding_adapter : optional
        Adapter with an ``async embed(texts, model)`` method.
    rerank_adapter : optional
        Adapter with an ``async rerank(query, texts, model, top_k)`` method.
    llm_adapter : optional
        Adapter with an ``async chat(messages, ...)`` method.
    """

    def __init__(
        self,
        vector_store=None,
        es_store=None,
        graph_store=None,
        embedding_adapter=None,
        rerank_adapter=None,
        llm_adapter=None,
    ):
        self.vector_store = vector_store
        self.es_store = es_store
        self.graph_store = graph_store
        self.embedding_adapter = embedding_adapter
        self.reranker = Reranker(rerank_adapter) if rerank_adapter else None
        self.llm_adapter = llm_adapter

        # LightRAG dual-level retriever (keyword extraction + graph search)
        self.dual_retriever = DualLevelRetriever(
            vector_store=vector_store,
            graph_store=graph_store,
            es_store=es_store,
            llm_adapter=llm_adapter,
        )

        # Graph retriever for local/global/hybrid LightRAG modes
        self._graph_retriever = (
            GraphRetriever(graph_store, vector_store) if graph_store else None
        )

    async def query(
        self,
        query: str,
        knowledge_base_id: str,
        collection_name: str,
        es_index: str = "",
        strategy: str = "hybrid",
        top_k: int = 5,
        rerank: bool = False,
        graph_enabled: bool = False,
        retrieval_mode: str = "hybrid",
        system_prompt: str = "",
    ) -> dict:
        """Execute full RAG pipeline: retrieve -> rerank -> generate.

        Args:
            retrieval_mode: LightRAG mode -- 'naive', 'local', 'global', 'hybrid'.
        """
        sources: list[dict] = []
        context_parts: list[str] = []

        # Compute query embedding once
        query_embedding = None
        if self.embedding_adapter:
            embeddings = await self.embedding_adapter.embed([query], model=None)
            if embeddings:
                query_embedding = embeddings[0]

        # Step 1: Retrieve via appropriate strategy
        #
        # Dispatch logic (preserving the original HybridRetriever semantics):
        # - When ``strategy`` is explicitly set to a non-default value
        #   (vector / fulltext / hybrid / graph_rag), use the legacy path.
        # - When ``retrieval_mode`` is "naive", use pure vector search.
        # - When ``retrieval_mode`` is local/global/hybrid AND ``graph_enabled``
        #   is True, use LightRAG dual-level retrieval.
        # - Otherwise fall through to the legacy strategy path.
        mode = self._normalise_mode(retrieval_mode)

        if mode == RetrievalMode.NAIVE:
            sources = await self._retrieve_naive(
                query_embedding, collection_name, top_k,
            )
        elif (
            mode in (RetrievalMode.LOCAL, RetrievalMode.GLOBAL, RetrievalMode.HYBRID)
            and graph_enabled
        ):
            sources = await self._retrieve_lightrag(
                query, query_embedding, collection_name, es_index,
                knowledge_base_id, top_k, mode,
            )
        else:
            # Legacy path: vector / fulltext / hybrid / graph_rag strategies
            sources = await self._retrieve_legacy(
                query, query_embedding, knowledge_base_id,
                collection_name, es_index, strategy, top_k,
                graph_enabled, retrieval_mode,
            )

        context_parts = [r.get("content", "") for r in sources]

        # Step 2: Graph RAG enrichment (naive mode with graph supplement)
        if (
            graph_enabled
            and self.graph_store
            and mode == RetrievalMode.NAIVE
            and strategy not in ("graph_rag", "local", "global")
        ):
            graph_context = await self._get_graph_context(query)
            if graph_context:
                context_parts.append(graph_context)

        # Step 3: Rerank
        if rerank and self.reranker and sources:
            sources = await self.reranker.rerank(query, sources, top_k=top_k)
            context_parts = [r.get("content", "") for r in sources]

        # Step 4: Generate answer
        context = "\n\n---\n\n".join(context_parts[:top_k])
        answer, confidence = await self._generate(
            query, context, sources, system_prompt,
        )

        return {
            "answer": answer,
            "sources": [
                {
                    "content": s.get("content", ""),
                    "score": s.get("score", 0),
                    "metadata": s.get("metadata", {}),
                    "source_document": s.get("source_document", ""),
                    "page_number": s.get("page_number"),
                    "chunk_id": s.get("chunk_id", ""),
                    "confidence": s.get("confidence", s.get("score", 0)),
                }
                for s in sources[:top_k]
            ],
            "confidence": confidence,
            "strategy": strategy,
            "retrieval_mode": retrieval_mode,
        }

    # ------------------------------------------------------------------
    # Retrieval dispatchers
    # ------------------------------------------------------------------

    async def _retrieve_naive(
        self,
        query_embedding: Optional[list[float]],
        collection_name: str,
        top_k: int,
    ) -> list[dict]:
        """Naive retrieval: pure vector similarity."""
        return await self.dual_retriever.retrieve_naive(
            query_embedding, collection_name, dim=1536, top_k=top_k,
        )

    async def _retrieve_lightrag(
        self,
        query: str,
        query_embedding: Optional[list[float]],
        collection_name: str,
        es_index: str,
        knowledge_base_id: str,
        top_k: int,
        mode: RetrievalMode,
    ) -> list[dict]:
        """LightRAG dual-level retrieval with vector supplementation."""
        results = await self.dual_retriever.retrieve(
            query=query,
            query_embedding=query_embedding,
            collection_name=collection_name,
            es_index=es_index,
            knowledge_base_id=knowledge_base_id,
            top_k=top_k,
            mode=mode.value,
        )

        # Supplement with vector search if results are sparse
        if len(results) < top_k and query_embedding:
            vector_results = await self.dual_retriever.retrieve_naive(
                query_embedding, collection_name, 1536,
                top_k - len(results),
            )
            seen_ids = {r.get("id") for r in results}
            for vr in vector_results:
                if vr.get("id") not in seen_ids:
                    results.append(vr)

        return results[:top_k]

    async def _retrieve_legacy(
        self,
        query: str,
        query_embedding: Optional[list[float]],
        knowledge_base_id: str,
        collection_name: str,
        es_index: str,
        strategy: str,
        top_k: int,
        graph_enabled: bool = False,
        retrieval_mode: str = "hybrid",
        dim: int = 1536,
    ) -> list[dict]:
        """Legacy retrieval path (formerly HybridRetriever).

        Handles strategies: vector, fulltext, hybrid, graph_rag, and
        LightRAG-style graph modes (local/global/hybrid) when dispatched
        from the legacy code path.
        """
        if not self.vector_store or not query_embedding:
            return []

        # LightRAG-style graph modes via legacy path
        if retrieval_mode in ("local", "global", "hybrid") and graph_enabled:
            return await self._lightrag_retrieve(
                query, query_embedding, collection_name, dim, top_k, retrieval_mode,
            )

        if strategy == "vector":
            results = await self._vector_search(
                query_embedding, collection_name, dim, top_k,
            )
        elif strategy == "fulltext" and self.es_store:
            results = await self._fulltext_search(
                query, es_index, knowledge_base_id, top_k,
            )
        elif strategy == "hybrid" and self.es_store:
            vector_results = await self._vector_search(
                query_embedding, collection_name, dim, top_k,
            )
            fulltext_results = await self._fulltext_search(
                query, es_index, knowledge_base_id, top_k,
            )
            results = self._rrf_merge(vector_results, fulltext_results, top_k)
        elif strategy == "graph_rag" and graph_enabled:
            results = await self._graph_rag_search(
                query, query_embedding, collection_name,
                es_index, knowledge_base_id, dim, top_k,
            )
        else:
            # Default fallback: vector search
            results = await self._vector_search(
                query_embedding, collection_name, dim, top_k,
            )

        return self._enrich_with_citations(results)

    # ------------------------------------------------------------------
    # Legacy retrieval primitives (formerly in HybridRetriever)
    # ------------------------------------------------------------------

    async def _vector_search(
        self, query_embedding: list[float], collection_name: str,
        dim: int, top_k: int,
    ) -> list[dict]:
        """Pure vector similarity search."""
        return await self.vector_store.search(
            collection_name, query_embedding, top_k, dim,
        )

    async def _fulltext_search(
        self, query: str, es_index: str, kb_id: str, top_k: int,
    ) -> list[dict]:
        """Elasticsearch fulltext search."""
        return await self.es_store.search(es_index, query, kb_id, top_k)

    @staticmethod
    def _rrf_merge(
        vector_results: list[dict],
        fulltext_results: list[dict],
        top_k: int,
        k: int = 60,
    ) -> list[dict]:
        """Reciprocal Rank Fusion merge of two result lists."""
        scores: dict[str, float] = {}
        all_docs: dict[str, dict] = {}

        for rank, doc in enumerate(vector_results):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
            all_docs[doc_id] = doc

        for rank, doc in enumerate(fulltext_results):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
            all_docs[doc_id] = doc

        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]
        results = []
        for doc_id in sorted_ids:
            doc = all_docs[doc_id]
            doc["score"] = scores[doc_id]
            results.append(doc)
        return results

    async def _graph_rag_search(
        self,
        query: str,
        query_embedding: list[float],
        collection_name: str,
        es_index: str,
        kb_id: str,
        dim: int,
        top_k: int,
    ) -> list[dict]:
        """Graph RAG search: vector results enriched with graph context."""
        vector_results = await self._vector_search(
            query_embedding, collection_name, dim, top_k,
        )

        graph_context = ""
        if self.graph_store:
            entities = await self.graph_store.search_nodes(query, limit=5)
            if entities:
                graph_parts = []
                for entity in entities:
                    neighbors = await self.graph_store.get_neighbors(
                        entity["id"], depth=1,
                    )
                    graph_parts.append(
                        f"{entity['properties'].get('name', '')}: "
                        f"{entity['properties'].get('description', '')}"
                    )
                    for n in neighbors[:3]:
                        graph_parts.append(
                            f"  -> {n['properties'].get('name', '')}"
                        )
                graph_context = "\n".join(graph_parts)

        for doc in vector_results:
            doc["graph_context"] = graph_context

        return vector_results

    async def _lightrag_retrieve(
        self,
        query: str,
        query_embedding: list[float],
        collection_name: str,
        dim: int,
        top_k: int,
        mode: str,
    ) -> list[dict]:
        """LightRAG-style retrieval: graph retrieval supplemented with vector search."""
        results: list[dict] = []

        if self._graph_retriever:
            graph_results = await self._graph_retriever.retrieve(
                query=query,
                query_embedding=query_embedding,
                collection_name=collection_name,
                dim=dim,
                top_k=top_k,
                mode=mode,
            )
            results.extend(graph_results)

        # Supplement with vector search if graph didn't produce enough results
        if len(results) < top_k:
            vector_results = await self._vector_search(
                query_embedding, collection_name, dim, top_k - len(results),
            )
            seen_ids = {r["id"] for r in results}
            for vr in vector_results:
                if vr["id"] not in seen_ids:
                    results.append(vr)
                    seen_ids.add(vr["id"])

        return self._enrich_with_citations(results[:top_k])

    @staticmethod
    def _enrich_with_citations(results: list[dict]) -> list[dict]:
        """Enrich retrieval results with grounded citation metadata.

        Adds ``source_document``, ``page_number``, ``chunk_id``, and
        ``confidence`` fields to every result dict so downstream consumers
        can trace the provenance of each retrieved chunk.
        """
        enriched: list[dict] = []
        for doc in results:
            metadata = doc.get("metadata", {})
            doc["source_document"] = (
                doc.get("source_document")
                or metadata.get("source_document")
                or metadata.get("filename")
                or metadata.get("file_name")
                or ""
            )
            doc["page_number"] = (
                doc.get("page_number")
                or metadata.get("page_number")
                or metadata.get("page")
            )
            doc["chunk_id"] = (
                doc.get("chunk_id")
                or metadata.get("chunk_id")
                or doc.get("id", "")
            )
            doc["confidence"] = doc.get("confidence", doc.get("score", 0.0))
            enriched.append(doc)
        return enriched

    # ------------------------------------------------------------------
    # Graph context enrichment
    # ------------------------------------------------------------------

    async def _get_graph_context(self, query: str) -> str:
        """Extract entities from query and fetch graph context."""
        if not self.graph_store:
            return ""
        try:
            neighbors = await self.graph_store.get_neighbors(
                query, depth=1, limit=5,
            )
            if neighbors:
                parts = []
                for n in neighbors:
                    label = n.get("label", "")
                    props = n.get("properties", {})
                    parts.append(f"{label}: {props}")
                return "相关实体:\n" + "\n".join(parts)
        except Exception as e:
            logger.warning("Failed to get graph context: %s", e)
        return ""

    # ------------------------------------------------------------------
    # Answer generation
    # ------------------------------------------------------------------

    async def _generate(
        self,
        query: str,
        context: str,
        sources: list[dict],
        system_prompt: str,
    ) -> tuple[str, float]:
        """Generate answer from context using LLM.

        Returns (answer, confidence).
        """
        if not context:
            return "未找到相关信息。", 0.0

        if not self.llm_adapter:
            return f"找到 {len(sources)} 条相关信息，但未配置LLM生成回答。", 0.3

        prompt = (
            f"基于以下参考资料回答用户问题。"
            f"如果参考资料中没有相关信息，请说明。\n\n"
            f"参考资料：\n{context}\n\n"
            f"用户问题：{query}"
        )
        if system_prompt:
            prompt = f"{system_prompt}\n\n{prompt}"

        try:
            response = await self.llm_adapter.chat(
                messages=[{"role": "user", "content": prompt}],
                model=None,
                temperature=0.3,
                max_tokens=2000,
            )
            answer = response.content
            confidence = min(0.5 + len(sources) * 0.1, 0.95)
            return answer, confidence
        except Exception:
            return f"找到 {len(sources)} 条相关信息，但LLM生成失败。", 0.3

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise_mode(retrieval_mode: str) -> RetrievalMode:
        """Convert string mode to enum, defaulting to HYBRID."""
        try:
            return RetrievalMode(retrieval_mode)
        except ValueError:
            return RetrievalMode.HYBRID
