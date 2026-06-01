"""Unit tests for RAG Pipeline"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.engines.knowledge_engine.rag_pipeline import RAGPipeline


@pytest.fixture
def mock_embedding_adapter():
    adapter = AsyncMock()
    adapter.embed = AsyncMock(return_value=[[0.1] * 1536])
    return adapter


@pytest.fixture
def mock_vector_store():
    store = AsyncMock()
    store.search = AsyncMock(return_value=[
        {"id": "1", "score": 0.9, "content": "test content 1", "metadata": {}},
        {"id": "2", "score": 0.8, "content": "test content 2", "metadata": {}},
    ])
    return store


@pytest.fixture
def mock_llm_adapter():
    adapter = AsyncMock()
    response = MagicMock()
    response.content = "This is the answer based on context."
    response.model = "test-model"
    response.usage = MagicMock()
    response.usage.dict.return_value = {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}
    adapter.chat = AsyncMock(return_value=response)
    return adapter


@pytest.mark.asyncio
async def test_rag_pipeline_with_llm(mock_vector_store, mock_embedding_adapter, mock_llm_adapter):
    """Full RAG pipeline with retrieval + generation."""
    pipeline = RAGPipeline(
        vector_store=mock_vector_store,
        embedding_adapter=mock_embedding_adapter,
        llm_adapter=mock_llm_adapter,
    )
    result = await pipeline.query(
        query="test query",
        knowledge_base_id="kb1",
        collection_name="col1",
        strategy="vector",
        top_k=2,
    )
    assert result["answer"] == "This is the answer based on context."
    assert len(result["sources"]) == 2
    assert result["confidence"] > 0
    assert result["strategy"] == "vector"


@pytest.mark.asyncio
async def test_rag_pipeline_no_llm(mock_vector_store, mock_embedding_adapter):
    """RAG pipeline without LLM returns sources but no generated answer."""
    pipeline = RAGPipeline(
        vector_store=mock_vector_store,
        embedding_adapter=mock_embedding_adapter,
        llm_adapter=None,
    )
    result = await pipeline.query(
        query="test query",
        knowledge_base_id="kb1",
        collection_name="col1",
    )
    assert "找到" in result["answer"]
    assert len(result["sources"]) == 2
    assert result["confidence"] == 0.3


@pytest.mark.asyncio
async def test_rag_pipeline_no_results(mock_embedding_adapter, mock_llm_adapter):
    """RAG pipeline with no retrieval results."""
    empty_store = AsyncMock()
    empty_store.search = AsyncMock(return_value=[])

    pipeline = RAGPipeline(
        vector_store=empty_store,
        embedding_adapter=mock_embedding_adapter,
        llm_adapter=mock_llm_adapter,
    )
    result = await pipeline.query(
        query="test query",
        knowledge_base_id="kb1",
        collection_name="col1",
    )
    assert result["answer"] == "未找到相关信息。"
    assert result["confidence"] == 0.0
    assert len(result["sources"]) == 0


@pytest.mark.asyncio
async def test_rag_pipeline_no_vector_store():
    """RAG pipeline without vector store."""
    pipeline = RAGPipeline(vector_store=None)
    result = await pipeline.query(
        query="test",
        knowledge_base_id="kb1",
        collection_name="col1",
    )
    assert result["answer"] == "未找到相关信息。"


@pytest.mark.asyncio
async def test_rag_pipeline_graph_context(mock_vector_store, mock_embedding_adapter, mock_llm_adapter):
    """RAG pipeline with graph enrichment via naive mode."""
    graph_store = AsyncMock()
    graph_store.get_neighbors = AsyncMock(return_value=[
        {"id": "n1", "labels": ["Person"], "properties": {"name": "Alice"}, "depth": 1},
    ])
    graph_store.search_nodes = AsyncMock(return_value=[
        {"id": "e1", "labels": ["Person"], "properties": {"name": "Alice", "description": "test"}},
    ])

    pipeline = RAGPipeline(
        vector_store=mock_vector_store,
        embedding_adapter=mock_embedding_adapter,
        llm_adapter=mock_llm_adapter,
        graph_store=graph_store,
    )
    # naive mode + graph_enabled triggers legacy graph enrichment path
    result = await pipeline.query(
        query="test query",
        knowledge_base_id="kb1",
        collection_name="col1",
        graph_enabled=True,
        retrieval_mode="naive",
    )
    assert result["answer"] is not None
    # Graph enrichment uses get_neighbors in naive mode
    graph_store.get_neighbors.assert_called()
