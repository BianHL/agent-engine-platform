"""LightRAG-inspired dual-level retrieval: low-level entities + high-level themes.

Retrieval modes:
- naive:  plain vector similarity (no keyword extraction)
- local:  entity-focused – extract specific names, then search entity nodes
- global: theme-focused – extract broad concepts, then search relation edges
- hybrid: combine local + global via reciprocal-rank fusion (RRF)
"""

from __future__ import annotations

import json
import logging
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

class RetrievalMode(str, Enum):
    NAIVE = "naive"
    LOCAL = "local"
    GLOBAL = "global"
    HYBRID = "hybrid"


class ExtractedKeywords(BaseModel):
    """Keywords extracted from a query by the LLM."""
    low_level: list[str] = Field(
        default_factory=list,
        description="Specific entity names, proper nouns, IDs, etc.",
    )
    high_level: list[str] = Field(
        default_factory=list,
        description="Broad themes, concepts, topics, categories.",
    )


# ---------------------------------------------------------------------------
# DualLevelRetriever
# ---------------------------------------------------------------------------

class DualLevelRetriever:
    """Retrieve documents using LightRAG-style dual-level strategy.

    Parameters
    ----------
    vector_store : optional
        Object with an ``async search(collection, embedding, top_k, dim)`` method.
    graph_store : optional
        Object with ``search_nodes``, ``get_neighbors``, ``search_edges`` methods.
    es_store : optional
        Object with an ``async search(index, query, kb_id, top_k)`` method.
    llm_adapter : optional
        Object with an ``async chat(messages, ...)`` method for keyword extraction.
    """

    def __init__(
        self,
        vector_store=None,
        graph_store=None,
        es_store=None,
        llm_adapter=None,
    ):
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.es_store = es_store
        self.llm_adapter = llm_adapter

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def retrieve(
        self,
        query: str,
        query_embedding: Optional[list[float]] = None,
        *,
        collection_name: str = "",
        es_index: str = "",
        knowledge_base_id: str = "",
        dim: int = 1536,
        top_k: int = 5,
        mode: str = "hybrid",
    ) -> list[dict]:
        """Dispatch to the appropriate retrieval strategy.

        Returns a list of result dicts, each with at least ``id``, ``content``,
        ``score``, ``metadata`` keys.
        """
        mode_enum = RetrievalMode(mode)

        if mode_enum == RetrievalMode.NAIVE:
            return await self.retrieve_naive(
                query_embedding, collection_name, dim, top_k,
            )

        keywords = await self.extract_keywords(query, mode_enum)

        if mode_enum == RetrievalMode.LOCAL:
            return await self.retrieve_local(keywords, top_k)
        if mode_enum == RetrievalMode.GLOBAL:
            return await self.retrieve_global(keywords, top_k)

        # hybrid – combine both with RRF
        local_kw = ExtractedKeywords(
            low_level=keywords.low_level,
            high_level=keywords.high_level,
        )
        global_kw = ExtractedKeywords(
            low_level=keywords.low_level,
            high_level=keywords.high_level,
        )
        local_results = await self.retrieve_local(local_kw, top_k)
        global_results = await self.retrieve_global(global_kw, top_k)
        return self._rrf_fusion(local_results, global_results, top_k)

    # ------------------------------------------------------------------
    # Keyword extraction (LLM-powered)
    # ------------------------------------------------------------------

    async def extract_keywords(
        self, query: str, mode: RetrievalMode = RetrievalMode.HYBRID,
    ) -> ExtractedKeywords:
        """Use the LLM to extract low-level and high-level keywords.

        Falls back to a simple heuristic split when no LLM is configured.
        """
        if not self.llm_adapter:
            return self._heuristic_keywords(query)

        prompt = (
            "请从以下用户问题中提取两类关键词：\n"
            "1. low_level（底层关键词）：具体的实体名称、人名、地名、组织名、"
            "产品名、编号等专有名词。\n"
            "2. high_level（高层关键词）：抽象的主题、概念、类别、领域等。\n\n"
            "请严格返回如下 JSON 格式，不要附加任何其他文本：\n"
            '{"low_level": ["关键词1", ...], "high_level": ["关键词1", ...]}\n\n'
            f"用户问题：{query}"
        )

        try:
            response = await self.llm_adapter.chat(
                messages=[{"role": "user", "content": prompt}],
                model=None,
                temperature=0.0,
                max_tokens=500,
            )
            return self._parse_keyword_response(response.content)
        except Exception:
            logger.warning("LLM keyword extraction failed, using heuristic")
            return self._heuristic_keywords(query)

    # ------------------------------------------------------------------
    # Retrieval modes
    # ------------------------------------------------------------------

    async def retrieve_naive(
        self,
        query_embedding: Optional[list[float]],
        collection_name: str,
        dim: int,
        top_k: int,
    ) -> list[dict]:
        """Plain vector similarity search – no keyword extraction."""
        if not self.vector_store or not query_embedding:
            return []
        return await self.vector_store.search(
            collection_name, query_embedding, top_k, dim,
        )

    async def retrieve_low_level(
        self, keywords: ExtractedKeywords, top_k: int,
    ) -> list[dict]:
        """Search entity nodes via vector / graph similarity.

        Uses low-level keywords (entity names) to find matching graph nodes
        and their associated chunks.
        """
        if not self.graph_store or not keywords.low_level:
            return []
        return await self._search_entity_nodes(keywords.low_level, top_k)

    async def retrieve_high_level(
        self, keywords: ExtractedKeywords, top_k: int,
    ) -> list[dict]:
        """Search relation edges / theme nodes via graph traversal.

        Uses high-level keywords (themes, concepts) to find hub nodes and
        collect thematic context.
        """
        if not self.graph_store or not keywords.high_level:
            return []
        return await self._search_theme_nodes(keywords.high_level, top_k)

    async def retrieve_local(
        self, keywords: ExtractedKeywords, top_k: int,
    ) -> list[dict]:
        """Entity-focused retrieval: low-level keywords -> entity nodes."""
        results = await self.retrieve_low_level(keywords, top_k)
        # Supplement with ES fulltext on low-level keywords
        es_results = await self._es_search_keywords(
            keywords.low_level, top_k,
        )
        if es_results:
            results = self._rrf_fusion(results, es_results, top_k)
        return results

    async def retrieve_global(
        self, keywords: ExtractedKeywords, top_k: int,
    ) -> list[dict]:
        """Theme-focused retrieval: high-level keywords -> hub/theme nodes."""
        results = await self.retrieve_high_level(keywords, top_k)
        # Supplement with ES fulltext on high-level keywords
        es_results = await self._es_search_keywords(
            keywords.high_level, top_k,
        )
        if es_results:
            results = self._rrf_fusion(results, es_results, top_k)
        return results

    async def retrieve_hybrid(
        self, query: str, top_k: int,
    ) -> list[dict]:
        """Combine local + global results with RRF fusion."""
        keywords = await self.extract_keywords(query)
        local = await self.retrieve_local(keywords, top_k)
        global_ = await self.retrieve_global(keywords, top_k)
        return self._rrf_fusion(local, global_, top_k)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _search_entity_nodes(
        self, keywords: list[str], top_k: int,
    ) -> list[dict]:
        """Search graph for entity nodes matching the given keywords."""
        results: list[dict] = []
        seen_ids: set[str] = set()

        for kw in keywords:
            try:
                nodes = await self.graph_store.search_nodes(kw, limit=top_k)
                for node in nodes:
                    nid = node["id"]
                    if nid in seen_ids:
                        continue
                    seen_ids.add(nid)
                    props = node.get("properties", {})
                    results.append({
                        "id": nid,
                        "content": props.get("description", props.get("name", "")),
                        "score": 0.8,
                        "metadata": {
                            "source": "graph_local",
                            "entity_name": props.get("name", ""),
                            "entity_type": props.get("type", ""),
                        },
                        "source_document": props.get("source_document", ""),
                    })
            except Exception as e:
                logger.warning("Failed to search graph node for keyword '%s': %s", kw, e)
                continue
            if len(results) >= top_k:
                break

        return results[:top_k]

    async def _search_theme_nodes(
        self, keywords: list[str], top_k: int,
    ) -> list[dict]:
        """Search graph for theme/hub nodes and collect their neighborhoods."""
        results: list[dict] = []
        seen_ids: set[str] = set()

        for kw in keywords:
            try:
                seed_nodes = await self.graph_store.search_nodes(kw, limit=3)
                for seed in seed_nodes:
                    sid = seed["id"]
                    if sid in seen_ids:
                        continue
                    seen_ids.add(sid)

                    # Traverse 1-hop to gather theme context
                    neighbors = await self.graph_store.get_neighbors(sid, depth=1)
                    context_parts = []
                    seed_props = seed.get("properties", {})
                    context_parts.append(
                        f"[主题] {seed_props.get('name', '')}: "
                        f"{seed_props.get('description', '')}"
                    )
                    for n in neighbors[:5]:
                        n_props = n.get("properties", {})
                        context_parts.append(
                            f"  -> {n_props.get('name', '')}: "
                            f"{n_props.get('description', '')}"
                        )

                    results.append({
                        "id": f"theme_{sid}",
                        "content": "\n".join(context_parts),
                        "score": 0.7,
                        "metadata": {
                            "source": "graph_global",
                            "theme_keyword": kw,
                            "neighbor_count": len(neighbors),
                        },
                        "source_document": seed_props.get("source_document", ""),
                    })
            except Exception as e:
                logger.warning("Failed to search theme neighborhood for keyword '%s': %s", kw, e)
                continue
            if len(results) >= top_k:
                break

        return results[:top_k]

    async def _es_search_keywords(
        self, keywords: list[str], top_k: int,
    ) -> list[dict]:
        """Search Elasticsearch using the provided keywords."""
        if not self.es_store or not keywords:
            return []
        query_text = " ".join(keywords)
        try:
            return await self.es_store.search(
                "", query_text, "", top_k,
            )
        except Exception as e:
            logger.warning("ES keyword search failed: %s", e)
            return []

    @staticmethod
    def _heuristic_keywords(query: str) -> ExtractedKeywords:
        """Simple heuristic split when LLM is unavailable.

        Treats shorter tokens as low-level, longer phrases as high-level.
        """
        words = [w.strip() for w in query.split() if len(w.strip()) > 1]
        # Words with capitalised first letter or containing digits → low-level
        low = [
            w for w in words
            if w[0].isupper() or any(c.isdigit() for c in w)
        ]
        high = [w for w in words if w not in low]
        # If nothing split, put the full query in both buckets
        if not low and not high:
            low = [query]
            high = [query]
        elif not low:
            low = high[:1]
        elif not high:
            high = low[:1]
        return ExtractedKeywords(low_level=low, high_level=high)

    @staticmethod
    def _parse_keyword_response(content: str) -> ExtractedKeywords:
        """Parse the LLM keyword extraction response."""
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(content[start:end])
                return ExtractedKeywords(
                    low_level=data.get("low_level", []),
                    high_level=data.get("high_level", []),
                )
        except (json.JSONDecodeError, KeyError) as e:
            logger.debug("LLM keyword extraction parse failed, returning empty: %s", e)
        return ExtractedKeywords(low_level=[], high_level=[])

    @staticmethod
    def _rrf_fusion(
        list_a: list[dict],
        list_b: list[dict],
        top_k: int,
        k: int = 60,
    ) -> list[dict]:
        """Reciprocal Rank Fusion merge of two result lists."""
        scores: dict[str, float] = {}
        all_docs: dict[str, dict] = {}

        for rank, doc in enumerate(list_a):
            doc_id = doc.get("id", str(rank))
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
            all_docs[doc_id] = doc

        for rank, doc in enumerate(list_b):
            doc_id = doc.get("id", str(rank + len(list_a)))
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
            all_docs[doc_id] = doc

        sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)[:top_k]
        results = []
        for doc_id in sorted_ids:
            doc = all_docs[doc_id].copy()
            doc["score"] = scores[doc_id]
            results.append(doc)
        return results
