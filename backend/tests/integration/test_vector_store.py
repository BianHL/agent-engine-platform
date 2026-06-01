"""Integration tests for Milvus vector store operations (K-001 through K-004, K-024 through K-026).

These tests mock the Milvus client at the connection level while exercising
the actual MilvusVectorStore and HybridRetriever class methods.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.engines.knowledge_engine.storage.vector.milvus_store import MilvusVectorStore
from app.engines.knowledge_engine.retriever.retriever import HybridRetriever


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_hit(doc_id: str, score: float, content: str, metadata: dict | None = None):
    """Create a mock Milvus search hit."""
    hit = MagicMock()
    hit.id = doc_id
    hit.score = score
    hit.entity = {"content": content, "metadata": metadata or {}}
    return hit


def _make_mock_collection(name: str = "test_col"):
    """Create a mock Milvus Collection with common methods wired up."""
    col = MagicMock()
    col.name = name
    col.insert = MagicMock(return_value=None)
    col.flush = MagicMock(return_value=None)
    col.delete = MagicMock(return_value=None)
    col.load = MagicMock(return_value=None)
    col.create_index = MagicMock(return_value=None)
    col.search = MagicMock(return_value=[[]])  # empty result set by default
    return col


# ---------------------------------------------------------------------------
# K-001: create_collection
# ---------------------------------------------------------------------------

class TestCreateCollection:
    """K-001: MilvusVectorStore.create_collection delegates to pymilvus correctly."""

    @pytest.mark.asyncio
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.utility")
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.Collection")
    async def test_create_collection_new(self, mock_collection_cls, mock_utility):
        """Creating a collection that does not exist yet should build schema and index."""
        mock_utility.has_collection.return_value = False
        mock_col = _make_mock_collection("kb_col")
        mock_collection_cls.return_value = mock_col

        store = MilvusVectorStore()
        await store.create_collection("kb_col", dim=768)

        mock_utility.has_collection.assert_called_once_with("kb_col")
        mock_collection_cls.assert_called_once()
        # Schema should include an embedding field with dim=768
        call_kwargs = mock_collection_cls.call_args
        schema = call_kwargs.kwargs.get("schema") or call_kwargs[1].get("schema")
        field_names = [f.name for f in schema.fields]
        assert "embedding" in field_names
        assert "content" in field_names
        assert "metadata" in field_names
        # Index must be created for the embedding field
        mock_col.create_index.assert_called_once()
        index_call = mock_col.create_index.call_args
        assert index_call.kwargs.get("field_name") == "embedding" or index_call[0][0] == "embedding"
        # Collection must be loaded into memory
        mock_col.load.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.utility")
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.Collection")
    async def test_create_collection_existing(self, mock_collection_cls, mock_utility):
        """Creating a collection that already exists should load it without recreating."""
        mock_utility.has_collection.return_value = True
        mock_col = _make_mock_collection("kb_col")
        mock_collection_cls.return_value = mock_col

        store = MilvusVectorStore()
        await store.create_collection("kb_col", dim=768)

        mock_utility.has_collection.assert_called_once_with("kb_col")
        # Should NOT create index on an existing collection
        mock_col.create_index.assert_not_called()
        mock_col.load.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.utility")
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.Collection")
    async def test_create_collection_respects_dim(self, mock_collection_cls, mock_utility):
        """Dimension parameter is passed through to the FieldSchema."""
        mock_utility.has_collection.return_value = False
        mock_col = _make_mock_collection()
        mock_collection_cls.return_value = mock_col

        store = MilvusVectorStore()
        await store.create_collection("dim_test", dim=256)

        call_kwargs = mock_collection_cls.call_args
        schema = call_kwargs.kwargs.get("schema") or call_kwargs[1].get("schema")
        embedding_field = next(f for f in schema.fields if f.name == "embedding")
        assert embedding_field.params.get("dim") == 256


# ---------------------------------------------------------------------------
# K-002: insert
# ---------------------------------------------------------------------------

class TestInsert:
    """K-002: MilvusVectorStore.insert passes data to pymilvus Collection.insert."""

    @pytest.mark.asyncio
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.utility")
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.Collection")
    async def test_insert_calls_collection_insert(self, mock_collection_cls, mock_utility):
        """insert() should call collection.insert with ids, contents, metadatas, embeddings."""
        mock_utility.has_collection.return_value = True
        mock_col = _make_mock_collection("test_col")
        mock_collection_cls.return_value = mock_col

        store = MilvusVectorStore()
        ids = ["id1", "id2"]
        contents = ["hello", "world"]
        metadatas = [{"src": "a"}, {"src": "b"}]
        embeddings = [[0.1] * 8, [0.2] * 8]

        await store.insert("test_col", ids, contents, metadatas, embeddings, dim=8)

        mock_col.insert.assert_called_once()
        insert_args = mock_col.insert.call_args[0][0]
        assert insert_args[0] == ids
        assert insert_args[1] == contents
        assert insert_args[2] == metadatas
        assert insert_args[3] == embeddings

    @pytest.mark.asyncio
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.utility")
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.Collection")
    async def test_insert_flushes_after_write(self, mock_collection_cls, mock_utility):
        """insert() must flush the collection after inserting data."""
        mock_utility.has_collection.return_value = True
        mock_col = _make_mock_collection("test_col")
        mock_collection_cls.return_value = mock_col

        store = MilvusVectorStore()
        await store.insert("test_col", ["id1"], ["c"], [[{}]], [[0.1] * 4], dim=4)

        mock_col.flush.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.utility")
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.Collection")
    async def test_insert_empty_batch(self, mock_collection_cls, mock_utility):
        """insert() with empty lists should still delegate to collection.insert."""
        mock_utility.has_collection.return_value = True
        mock_col = _make_mock_collection("test_col")
        mock_collection_cls.return_value = mock_col

        store = MilvusVectorStore()
        await store.insert("test_col", [], [], [], [], dim=4)

        mock_col.insert.assert_called_once()
        mock_col.flush.assert_called_once()


# ---------------------------------------------------------------------------
# K-003: search
# ---------------------------------------------------------------------------

class TestSearch:
    """K-003: MilvusVectorStore.search returns ranked results from pymilvus."""

    @pytest.mark.asyncio
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.utility")
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.Collection")
    async def test_search_returns_ranked_results(self, mock_collection_cls, mock_utility):
        """search() should return results sorted by Milvus score (descending)."""
        mock_utility.has_collection.return_value = True
        hits = [
            _make_mock_hit("doc1", 0.95, "top result", {"page": 1}),
            _make_mock_hit("doc2", 0.80, "second result", {"page": 2}),
            _make_mock_hit("doc3", 0.60, "third result", {"page": 3}),
        ]
        mock_col = _make_mock_collection("test_col")
        mock_col.search = MagicMock(return_value=[hits])
        mock_collection_cls.return_value = mock_col

        store = MilvusVectorStore()
        results = await store.search("test_col", [0.1] * 8, top_k=3, dim=8)

        assert len(results) == 3
        # Results should preserve Milvus ordering (already ranked by score)
        assert results[0]["id"] == "doc1"
        assert results[0]["score"] == 0.95
        assert results[0]["content"] == "top result"
        assert results[0]["metadata"] == {"page": 1}
        assert results[1]["id"] == "doc2"
        assert results[2]["id"] == "doc3"

    @pytest.mark.asyncio
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.utility")
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.Collection")
    async def test_search_passes_correct_params(self, mock_collection_cls, mock_utility):
        """search() should pass top_k and embedding to pymilvus search."""
        mock_utility.has_collection.return_value = True
        mock_col = _make_mock_collection("test_col")
        mock_col.search = MagicMock(return_value=[[]])
        mock_collection_cls.return_value = mock_col

        store = MilvusVectorStore()
        query_emb = [0.5] * 8
        await store.search("test_col", query_emb, top_k=10, dim=8)

        mock_col.search.assert_called_once()
        call_kwargs = mock_col.search.call_args
        assert call_kwargs.kwargs.get("data") == [query_emb] or call_kwargs[0][0] == [query_emb]
        assert call_kwargs.kwargs.get("limit") == 10 or call_kwargs[0][3] == 10

    @pytest.mark.asyncio
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.utility")
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.Collection")
    async def test_search_empty_results(self, mock_collection_cls, mock_utility):
        """search() should return an empty list when Milvus returns no hits."""
        mock_utility.has_collection.return_value = True
        mock_col = _make_mock_collection("test_col")
        mock_col.search = MagicMock(return_value=[[]])
        mock_collection_cls.return_value = mock_col

        store = MilvusVectorStore()
        results = await store.search("test_col", [0.1] * 8, top_k=5, dim=8)

        assert results == []

    @pytest.mark.asyncio
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.utility")
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.Collection")
    async def test_search_output_fields_include_content_and_metadata(
        self, mock_collection_cls, mock_utility
    ):
        """search() should request content and metadata as output fields."""
        mock_utility.has_collection.return_value = True
        mock_col = _make_mock_collection("test_col")
        mock_col.search = MagicMock(return_value=[[]])
        mock_collection_cls.return_value = mock_col

        store = MilvusVectorStore()
        await store.search("test_col", [0.1] * 4, top_k=3, dim=4)

        call_kwargs = mock_col.search.call_args
        output_fields = call_kwargs.kwargs.get("output_fields") or call_kwargs[0][4]
        assert "content" in output_fields
        assert "metadata" in output_fields


# ---------------------------------------------------------------------------
# K-004: delete
# ---------------------------------------------------------------------------

class TestDelete:
    """K-004: MilvusVectorStore.delete calls collection.delete with correct expression."""

    @pytest.mark.asyncio
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.utility")
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.Collection")
    async def test_delete_calls_with_id_expression(self, mock_collection_cls, mock_utility):
        """delete() should construct an 'id in [...]' expression and pass it to collection.delete."""
        mock_utility.has_collection.return_value = True
        mock_col = _make_mock_collection("test_col")
        mock_collection_cls.return_value = mock_col

        store = MilvusVectorStore()
        await store.delete("test_col", ["id1", "id2", "id3"], dim=8)

        mock_col.delete.assert_called_once()
        delete_expr = mock_col.delete.call_args[0][0]
        assert "id1" in delete_expr
        assert "id2" in delete_expr
        assert "id3" in delete_expr
        assert delete_expr.startswith("id in")

    @pytest.mark.asyncio
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.utility")
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.Collection")
    async def test_delete_single_id(self, mock_collection_cls, mock_utility):
        """delete() should work with a single-element id list."""
        mock_utility.has_collection.return_value = True
        mock_col = _make_mock_collection("test_col")
        mock_collection_cls.return_value = mock_col

        store = MilvusVectorStore()
        await store.delete("test_col", ["only_id"], dim=8)

        mock_col.delete.assert_called_once()
        delete_expr = mock_col.delete.call_args[0][0]
        assert "only_id" in delete_expr


# ---------------------------------------------------------------------------
# K-011: Tenant isolation in collection names
# ---------------------------------------------------------------------------

class TestTenantIsolation:
    """K-011: Collection names must encode tenant context to prevent cross-tenant access."""

    @pytest.mark.asyncio
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.utility")
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.Collection")
    async def test_different_tenants_use_different_collections(
        self, mock_collection_cls, mock_utility
    ):
        """Two tenants should never share the same collection name."""
        mock_utility.has_collection.return_value = False
        mock_col = _make_mock_collection()
        mock_collection_cls.return_value = mock_col

        store = MilvusVectorStore()

        # Simulate tenant-prefixed collection naming convention
        tenant_a_col = "tenant_alpha_kb_main"
        tenant_b_col = "tenant_beta_kb_main"

        await store.create_collection(tenant_a_col, dim=768)
        await store.create_collection(tenant_b_col, dim=768)

        # Each call should have used a distinct collection name
        calls = mock_collection_cls.call_args_list
        names_used = []
        for call in calls:
            names_used.append(call.kwargs.get("name") or call[1].get("name", call[0][0]))
        assert tenant_a_col in names_used
        assert tenant_b_col in names_used
        assert tenant_a_col != tenant_b_col

    @pytest.mark.asyncio
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.utility")
    @patch("app.engines.knowledge_engine.storage.vector.milvus_store.Collection")
    async def test_search_scoped_to_tenant_collection(self, mock_collection_cls, mock_utility):
        """Search operations should target the tenant-specific collection, not a shared one."""
        mock_utility.has_collection.return_value = True
        mock_col = _make_mock_collection()
        mock_col.search = MagicMock(return_value=[[]])
        mock_collection_cls.return_value = mock_col

        store = MilvusVectorStore()
        tenant_col = "tenant_acme_kb_docs"
        await store.search(tenant_col, [0.1] * 4, top_k=5, dim=4)

        # The Collection was constructed with the tenant-specific name
        call_name = mock_collection_cls.call_args.kwargs.get("name") or mock_collection_cls.call_args[0][0]
        assert call_name == tenant_col


# ---------------------------------------------------------------------------
# K-024 / K-026: HybridRetriever vector-only fallback
# ---------------------------------------------------------------------------

class TestHybridRetrieverFallback:
    """K-024 / K-026: HybridRetriever falls back to vector search when es_store is None."""

    @pytest.mark.asyncio
    async def test_hybrid_strategy_falls_back_to_vector_when_no_es(self):
        """With es_store=None and strategy='hybrid', retriever should use vector search only."""
        vector_store = AsyncMock()
        vector_store.search.return_value = [
            {"id": "v1", "score": 0.9, "content": "vector hit", "metadata": {}},
        ]

        retriever = HybridRetriever(vector_store=vector_store, es_store=None)
        results = await retriever.retrieve(
            query="test query",
            query_embedding=[0.1] * 8,
            knowledge_base_id="kb1",
            collection_name="col1",
            es_index="idx1",
            dim=8,
            top_k=5,
            strategy="hybrid",
        )

        # Should have fallen back to vector search
        vector_store.search.assert_called_once_with("col1", [0.1] * 8, 5, 8)
        assert len(results) == 1
        assert results[0]["id"] == "v1"

    @pytest.mark.asyncio
    async def test_fulltext_strategy_falls_back_to_vector_when_no_es(self):
        """With es_store=None and strategy='fulltext', retriever should use vector search only."""
        vector_store = AsyncMock()
        vector_store.search.return_value = [
            {"id": "v2", "score": 0.85, "content": "fallback", "metadata": {}},
        ]

        retriever = HybridRetriever(vector_store=vector_store, es_store=None)
        results = await retriever.retrieve(
            query="another query",
            query_embedding=[0.2] * 8,
            knowledge_base_id="kb1",
            collection_name="col1",
            es_index="idx1",
            dim=8,
            top_k=3,
            strategy="fulltext",
        )

        vector_store.search.assert_called_once()
        assert len(results) == 1
        assert results[0]["id"] == "v2"

    @pytest.mark.asyncio
    async def test_vector_strategy_uses_vector_store_directly(self):
        """With strategy='vector', retriever should always use vector search regardless of es_store."""
        vector_store = AsyncMock()
        vector_store.search.return_value = [
            {"id": "d1", "score": 0.99, "content": "direct", "metadata": {}},
        ]
        es_store = AsyncMock()

        retriever = HybridRetriever(vector_store=vector_store, es_store=es_store)
        results = await retriever.retrieve(
            query="q",
            query_embedding=[0.3] * 8,
            knowledge_base_id="kb1",
            collection_name="col1",
            es_index="idx1",
            dim=8,
            top_k=5,
            strategy="vector",
        )

        # ES should NOT be called for vector-only strategy
        es_store.search.assert_not_called()
        vector_store.search.assert_called_once()
        assert results[0]["id"] == "d1"

    @pytest.mark.asyncio
    async def test_default_strategy_is_hybrid(self):
        """Default strategy should be 'hybrid', which falls back to vector when es_store=None."""
        vector_store = AsyncMock()
        vector_store.search.return_value = [
            {"id": "x1", "score": 0.7, "content": "default", "metadata": {}},
        ]

        retriever = HybridRetriever(vector_store=vector_store, es_store=None)
        results = await retriever.retrieve(
            query="default query",
            query_embedding=[0.4] * 8,
            knowledge_base_id="kb1",
            collection_name="col1",
            es_index="idx1",
            dim=8,
        )

        vector_store.search.assert_called_once()
        assert len(results) == 1
