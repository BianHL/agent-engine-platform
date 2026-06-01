"""
Integration-level tests for ESStore (Elasticsearch store).

K-009: ESStore.create_index() with mocked ES client
K-010: ESStore.search() full-text search returns results
K-011: Tenant isolation in index names
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.engines.knowledge_engine.storage.search.es_store import ESStore


@pytest.fixture
def mock_es_client():
    """Create a mock AsyncElasticsearch client."""
    client = AsyncMock()
    client.indices = MagicMock()
    client.indices.create = AsyncMock()
    client.indices.delete = AsyncMock()
    client.index = AsyncMock()
    client.search = AsyncMock()
    client.delete = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def es_store(mock_es_client):
    """Create an ESStore instance with a mocked client already connected."""
    store = ESStore(hosts="http://test-es:9200")
    store._client = mock_es_client
    return store


# ---------------------------------------------------------------------------
# K-009: create_index
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_index_calls_client_with_correct_body(es_store, mock_es_client):
    """K-009: create_index should build the expected settings/mappings body."""
    await es_store.create_index("test_index")

    mock_es_client.indices.create.assert_awaited_once()
    call_kwargs = mock_es_client.indices.create.call_args[1]
    assert call_kwargs["index"] == "test_index"

    body = call_kwargs["body"]
    assert body["settings"]["number_of_shards"] == 1
    assert body["settings"]["number_of_replicas"] == 0
    assert body["mappings"]["properties"]["content"]["type"] == "text"
    assert body["mappings"]["properties"]["knowledge_base_id"]["type"] == "keyword"
    assert body["mappings"]["properties"]["document_id"]["type"] == "keyword"
    assert body["mappings"]["properties"]["chunk_id"]["type"] == "keyword"


@pytest.mark.asyncio
async def test_create_index_propagates_client_error(es_store, mock_es_client):
    """K-009: create_index should propagate exceptions from the ES client."""
    mock_es_client.indices.create.side_effect = ConnectionError("ES unavailable")

    with pytest.raises(ConnectionError, match="ES unavailable"):
        await es_store.create_index("bad_index")


# ---------------------------------------------------------------------------
# K-010: search
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_returns_parsed_hits(es_store, mock_es_client):
    """K-010: search should return a list of dicts with id, score, content, metadata."""
    mock_es_client.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_id": "doc-1",
                    "_score": 1.5,
                    "_source": {"content": "hello world", "metadata": {"page": 1}},
                },
                {
                    "_id": "doc-2",
                    "_score": 0.8,
                    "_source": {"content": "world peace", "metadata": {}},
                },
            ]
        }
    }

    results = await es_store.search("my_index", query="world", top_k=5)

    assert len(results) == 2
    assert results[0]["id"] == "doc-1"
    assert results[0]["score"] == 1.5
    assert results[0]["content"] == "hello world"
    assert results[0]["metadata"] == {"page": 1}
    assert results[1]["id"] == "doc-2"
    assert results[1]["content"] == "world peace"


@pytest.mark.asyncio
async def test_search_returns_empty_when_no_hits(es_store, mock_es_client):
    """K-010: search should return an empty list when no documents match."""
    mock_es_client.search.return_value = {"hits": {"hits": []}}

    results = await es_store.search("my_index", query="nonexistent")

    assert results == []


@pytest.mark.asyncio
async def test_search_builds_bool_query_with_content_match(es_store, mock_es_client):
    """K-010: search must send a bool/must query with a content match clause."""
    mock_es_client.search.return_value = {"hits": {"hits": []}}

    await es_store.search("idx", query="test query", top_k=10)

    call_kwargs = mock_es_client.search.call_args[1]
    body = call_kwargs["body"]
    must_clauses = body["query"]["bool"]["must"]

    assert any(c.get("match", {}).get("content") == "test query" for c in must_clauses)
    assert body["size"] == 10
    assert body["_source"] == ["content", "metadata"]


@pytest.mark.asyncio
async def test_search_filters_by_knowledge_base_id(es_store, mock_es_client):
    """K-010: search should add a knowledge_base_id term filter when provided."""
    mock_es_client.search.return_value = {"hits": {"hits": []}}

    await es_store.search("idx", query="q", knowledge_base_id="kb-42")

    body = mock_es_client.search.call_args[1]["body"]
    must_clauses = body["query"]["bool"]["must"]

    kb_filter = next(
        (c for c in must_clauses if "term" in c and "knowledge_base_id" in c["term"]),
        None,
    )
    assert kb_filter is not None
    assert kb_filter["term"]["knowledge_base_id"] == "kb-42"


@pytest.mark.asyncio
async def test_search_omits_kb_filter_when_not_provided(es_store, mock_es_client):
    """K-010: search should not include a knowledge_base_id filter when it is None."""
    mock_es_client.search.return_value = {"hits": {"hits": []}}

    await es_store.search("idx", query="q")

    body = mock_es_client.search.call_args[1]["body"]
    must_clauses = body["query"]["bool"]["must"]

    kb_filters = [c for c in must_clauses if "term" in c and "knowledge_base_id" in c.get("term", {})]
    assert kb_filters == []


# ---------------------------------------------------------------------------
# index_document (insert)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_index_document_calls_client(es_store, mock_es_client):
    """index_document should forward index name, doc id, and document body."""
    doc = {"content": "some text", "metadata": {"source": "pdf"}}

    await es_store.index_document("my_index", "doc-99", doc)

    mock_es_client.index.assert_awaited_once_with(
        index="my_index", id="doc-99", document=doc
    )


@pytest.mark.asyncio
async def test_index_document_propagates_error(es_store, mock_es_client):
    """index_document should propagate ES client exceptions."""
    mock_es_client.index.side_effect = Exception("indexing failed")

    with pytest.raises(Exception, match="indexing failed"):
        await es_store.index_document("idx", "id", {})


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_calls_client_with_ignore_404(es_store, mock_es_client):
    """delete should pass ignore=[404] so missing docs don't raise."""
    await es_store.delete("my_index", "doc-10")

    mock_es_client.delete.assert_awaited_once_with(
        index="my_index", id="doc-10", ignore=[404]
    )


@pytest.mark.asyncio
async def test_delete_does_not_raise_on_missing_document(es_store, mock_es_client):
    """delete should silently succeed when the document does not exist."""
    # ignore=[404] means ES won't raise; the mock just returns normally
    mock_es_client.delete.return_value = None

    # Should not raise
    await es_store.delete("my_index", "nonexistent-id")

    mock_es_client.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_propagates_non_404_errors(es_store, mock_es_client):
    """delete should still propagate real errors (e.g. connection failure)."""
    mock_es_client.delete.side_effect = ConnectionError("ES down")

    with pytest.raises(ConnectionError):
        await es_store.delete("my_index", "doc-1")


# ---------------------------------------------------------------------------
# K-011: Tenant isolation in index names
# ---------------------------------------------------------------------------


def _index_for_tenant(tenant_id: str) -> str:
    """Helper: derive the expected index name for a given tenant."""
    return f"kb_{tenant_id}"


@pytest.mark.asyncio
async def test_tenant_isolation_create_index(es_store, mock_es_client):
    """K-011: Different tenants must use different index names."""
    await es_store.create_index(_index_for_tenant("tenant-a"))
    await es_store.create_index(_index_for_tenant("tenant-b"))

    calls = mock_es_client.indices.create.call_args_list
    index_a = calls[0][1]["index"]
    index_b = calls[1][1]["index"]

    assert index_a != index_b
    assert "tenant-a" in index_a
    assert "tenant-b" in index_b


@pytest.mark.asyncio
async def test_tenant_isolation_search(es_store, mock_es_client):
    """K-011: Searches scoped to one tenant index must not leak to another."""
    mock_es_client.search.return_value = {"hits": {"hits": []}}

    # Search only in tenant-a's index
    await es_store.search(_index_for_tenant("tenant-a"), query="secret")

    called_index = mock_es_client.search.call_args[1]["index"]
    assert "tenant-a" in called_index
    assert "tenant-b" not in called_index


@pytest.mark.asyncio
async def test_tenant_isolation_insert(es_store, mock_es_client):
    """K-011: Documents inserted into tenant-a's index must use tenant-a's index name."""
    doc = {"content": "confidential data"}

    await es_store.index_document(
        _index_for_tenant("tenant-a"), "doc-1", doc
    )

    called_index = mock_es_client.index.call_args[1]["index"]
    assert called_index == "kb_tenant-a"
    assert "tenant-b" not in called_index


@pytest.mark.asyncio
async def test_tenant_isolation_delete(es_store, mock_es_client):
    """K-011: Deleting from tenant-a's index must not affect tenant-b's index."""
    await es_store.delete(_index_for_tenant("tenant-a"), "doc-1")

    called_index = mock_es_client.delete.call_args[1]["index"]
    assert called_index == "kb_tenant-a"


@pytest.mark.asyncio
async def test_tenant_isolation_delete_index(es_store, mock_es_client):
    """K-011: Deleting tenant-a's index must pass the correct index name."""
    await es_store.delete_index(_index_for_tenant("tenant-a"))

    called_index = mock_es_client.indices.delete.call_args[1]["index"]
    assert called_index == "kb_tenant-a"


# ---------------------------------------------------------------------------
# connect / close lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connect_creates_client():
    """connect() should create an AsyncElasticsearch client."""
    store = ESStore(hosts="http://localhost:9200")
    with patch(
        "app.engines.knowledge_engine.storage.search.es_store.AsyncElasticsearch"
    ) as MockClient:
        mock_instance = AsyncMock()
        MockClient.return_value = mock_instance

        await store.connect()

        MockClient.assert_called_once_with(hosts="http://localhost:9200")
        assert store._client is mock_instance


@pytest.mark.asyncio
async def test_close_closes_client(es_store, mock_es_client):
    """close() should call close on the underlying client."""
    await es_store.close()

    mock_es_client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_noop_when_not_connected():
    """close() should not raise when the client was never connected."""
    store = ESStore()
    # _client is None by default; close should be a no-op
    await store.close()
