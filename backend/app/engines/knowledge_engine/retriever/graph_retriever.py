"""LightRAG-style dual-level graph retrieval: Local, Global, and Hybrid modes."""

from typing import Optional


class GraphRetriever:
    """Implements LightRAG-style graph retrieval with Local, Global, and Hybrid modes.

    - Local: Given query entities, traverse neighbors (1-2 hops) to find related
      entities and their associated chunks.
    - Global: Find high-degree hub nodes thematically related to the query,
      then collect their connected chunks.
    - Hybrid: Weighted merge of Local + Global results.
    """

    def __init__(self, graph_store, vector_store=None):
        self.graph_store = graph_store
        self.vector_store = vector_store

    async def retrieve(
        self,
        query: str,
        query_embedding: Optional[list[float]] = None,
        collection_name: str = "",
        dim: int = 1536,
        top_k: int = 5,
        mode: str = "hybrid",
        local_weight: float = 0.6,
    ) -> list[dict]:
        """Retrieve using the specified graph retrieval mode.

        Args:
            query: User query text.
            query_embedding: Optional vector embedding for fallback search.
            collection_name: Milvus collection name for vector fallback.
            dim: Embedding dimension.
            top_k: Maximum results to return.
            mode: One of 'local', 'global', 'hybrid'.
            local_weight: Weight for local results in hybrid merge (0-1).

        Returns:
            List of result dicts with content, score, metadata, source info.
        """
        if mode == "local":
            return await self._local_retrieve(query, top_k)
        elif mode == "global":
            return await self._global_retrieve(query, top_k)
        else:  # hybrid
            local_results = await self._local_retrieve(query, top_k)
            global_results = await self._global_retrieve(query, top_k)
            return self._weighted_merge(
                local_results, global_results, top_k, local_weight
            )

    async def _local_retrieve(self, query: str, top_k: int) -> list[dict]:
        """Local retrieval: find query entities, traverse 1-2 hops for related
        entities, collect their associated chunks."""
        if not self.graph_store:
            return []

        try:
            # Step 1: Find entities matching the query
            seed_entities = await self.graph_store.search_nodes(query, limit=5)
            if not seed_entities:
                return []

            # Step 2: Traverse neighbors (1-2 hops) from each seed entity
            all_neighbor_ids = set()
            entity_context_parts = []

            for entity in seed_entities:
                eid = entity["id"]
                name = entity["properties"].get("name", "")
                desc = entity["properties"].get("description", "")
                entity_context_parts.append(f"[实体] {name}: {desc}")

                # 1-hop neighbors
                neighbors_depth1 = await self.graph_store.get_neighbors(
                    eid, depth=1
                )
                for n in neighbors_depth1:
                    nid = n["id"]
                    if nid not in all_neighbor_ids:
                        all_neighbor_ids.add(nid)
                        n_name = n["properties"].get("name", "")
                        n_desc = n["properties"].get("description", "")
                        entity_context_parts.append(
                            f"  -> {n_name}: {n_desc}"
                        )

                # 2-hop neighbors
                neighbors_depth2 = await self.graph_store.get_neighbors(
                    eid, depth=2
                )
                for n in neighbors_depth2:
                    nid = n["id"]
                    if nid not in all_neighbor_ids:
                        all_neighbor_ids.add(nid)
                        n_name = n["properties"].get("name", "")
                        n_desc = n["properties"].get("description", "")
                        entity_context_parts.append(
                            f"    ->> {n_name}: {n_desc}"
                        )

            # Step 3: Collect chunks associated with discovered entities
            chunks = await self._collect_chunks_from_entities(
                list(all_neighbor_ids) + [e["id"] for e in seed_entities],
                top_k,
            )

            # If no chunks found from graph, return entity context as content
            if not chunks:
                graph_text = "\n".join(entity_context_parts)
                return [
                    {
                        "id": f"graph_local_{seed_entities[0]['id']}",
                        "content": graph_text,
                        "score": 0.8,
                        "metadata": {
                            "source": "graph_local",
                            "entity_count": len(seed_entities),
                            "neighbor_count": len(all_neighbor_ids),
                        },
                        "source_document": "knowledge_graph",
                        "chunk_id": f"graph_local_{seed_entities[0]['id']}",
                        "confidence": 0.8,
                    }
                ]

            return chunks

        except Exception:
            return []

    async def _global_retrieve(self, query: str, top_k: int) -> list[dict]:
        """Global retrieval: find high-degree hub nodes related to the query,
        then collect their connected chunks."""
        if not self.graph_store:
            return []

        try:
            # Step 1: Find entities matching the query
            seed_entities = await self.graph_store.search_nodes(query, limit=3)
            if not seed_entities:
                return []

            # Step 2: Find hub nodes - entities with high connectivity
            hub_nodes = await self._find_hub_nodes(seed_entities, max_hubs=5)

            # Step 3: Collect chunks from hub nodes and their neighborhoods
            hub_ids = [h["id"] for h in hub_nodes]
            hub_context_parts = []
            for hub in hub_nodes:
                name = hub["properties"].get("name", "")
                desc = hub["properties"].get("description", "")
                degree = hub.get("degree", 0)
                hub_context_parts.append(
                    f"[枢纽节点] {name} (度={degree}): {desc}"
                )

            # Collect chunks from hub neighborhoods
            all_ids = list(set(hub_ids + [e["id"] for e in seed_entities]))
            chunks = await self._collect_chunks_from_entities(all_ids, top_k)

            if not chunks:
                graph_text = "\n".join(hub_context_parts)
                return [
                    {
                        "id": f"graph_global_{seed_entities[0]['id']}",
                        "content": graph_text,
                        "score": 0.7,
                        "metadata": {
                            "source": "graph_global",
                            "hub_count": len(hub_nodes),
                        },
                        "source_document": "knowledge_graph",
                        "chunk_id": f"graph_global_{seed_entities[0]['id']}",
                        "confidence": 0.7,
                    }
                ]

            return chunks

        except Exception:
            return []

    async def _find_hub_nodes(
        self, seed_entities: list[dict], max_hubs: int = 5
    ) -> list[dict]:
        """Find high-degree hub nodes near seed entities."""
        hub_candidates = []

        for entity in seed_entities:
            eid = entity["id"]
            neighbors = await self.graph_store.get_neighbors(eid, depth=1)
            # Count connections per neighbor (approximate degree)
            for n in neighbors:
                n_id = n["id"]
                n_neighbors = await self.graph_store.get_neighbors(n_id, depth=1)
                degree = len(n_neighbors)
                hub_candidates.append(
                    {**n, "degree": degree}
                )

            # Also include the seed entity itself
            seed_neighbors = await self.graph_store.get_neighbors(eid, depth=1)
            hub_candidates.append(
                {**entity, "degree": len(seed_neighbors)}
            )

        # Sort by degree descending, deduplicate, take top hubs
        seen_ids = set()
        hubs = []
        for h in sorted(hub_candidates, key=lambda x: x["degree"], reverse=True):
            if h["id"] not in seen_ids:
                seen_ids.add(h["id"])
                hubs.append(h)
                if len(hubs) >= max_hubs:
                    break

        return hubs

    async def _collect_chunks_from_entities(
        self, entity_ids: list[str], top_k: int
    ) -> list[dict]:
        """Collect document chunks associated with the given entity IDs.

        Looks for chunks referenced in entity properties or relationships.
        """
        chunks = []
        seen_chunk_ids = set()

        for eid in entity_ids:
            try:
                # Get the entity and check for chunk references in properties
                neighbors = await self.graph_store.get_neighbors(eid, depth=1)
                for n in neighbors:
                    props = n.get("properties", {})
                    # Check if this neighbor is a Document or has chunk references
                    labels = n.get("labels", [])
                    if "Document" in labels:
                        chunk_id = props.get("chunk_id", n["id"])
                        if chunk_id not in seen_chunk_ids:
                            seen_chunk_ids.add(chunk_id)
                            chunks.append(
                                {
                                    "id": chunk_id,
                                    "content": props.get("content", props.get("text", "")),
                                    "score": 0.75,
                                    "metadata": {
                                        "source": "graph_traversal",
                                        "entity_id": eid,
                                        "neighbor_labels": labels,
                                    },
                                    "source_document": props.get("source_document", props.get("filename", "")),
                                    "page_number": props.get("page_number"),
                                    "chunk_id": chunk_id,
                                    "confidence": 0.75,
                                }
                            )
            except Exception:
                continue

            if len(chunks) >= top_k:
                break

        return chunks[:top_k]

    def _weighted_merge(
        self,
        local_results: list[dict],
        global_results: list[dict],
        top_k: int,
        local_weight: float = 0.6,
    ) -> list[dict]:
        """Weighted merge of local and global results."""
        global_weight = 1.0 - local_weight
        scores = {}
        all_docs = {}

        for doc in local_results:
            doc_id = doc["id"]
            weighted_score = doc.get("score", 0) * local_weight
            if doc_id in scores:
                scores[doc_id] += weighted_score
            else:
                scores[doc_id] = weighted_score
                all_docs[doc_id] = doc

        for doc in global_results:
            doc_id = doc["id"]
            weighted_score = doc.get("score", 0) * global_weight
            if doc_id in scores:
                scores[doc_id] += weighted_score
            else:
                scores[doc_id] = weighted_score
                all_docs[doc_id] = doc

        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[
            :top_k
        ]

        results = []
        for doc_id in sorted_ids:
            doc = all_docs[doc_id].copy()
            doc["score"] = scores[doc_id]
            doc["confidence"] = scores[doc_id]
            doc["metadata"] = doc.get("metadata", {})
            doc["metadata"]["retrieval_mode"] = "hybrid_graph"
            results.append(doc)

        return results
