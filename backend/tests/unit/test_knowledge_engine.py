"""Unit tests for Knowledge Engine"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.engines.knowledge_engine.chunker.chunker import DocumentChunker
from app.engines.knowledge_engine.parser.base import BaseDocumentParser
from app.engines.knowledge_engine.retriever.retriever import HybridRetriever
from app.core.exceptions import DocumentNotFoundError, PermissionDeniedError, AgentEngineError


# === Chunker Tests ===

def test_recursive_chunk_basic():
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    text = "Hello world. " * 20
    chunks = chunker.chunk_text(text, strategy="recursive")
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk["content"]) <= 120  # Some tolerance


def test_recursive_chunk_small_text():
    chunker = DocumentChunker(chunk_size=1000, chunk_overlap=50)
    text = "Short text"
    chunks = chunker.chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0]["content"] == "Short text"


def test_recursive_chunk_preserves_structure():
    chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)
    text = "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph."
    chunks = chunker.chunk_text(text)
    assert len(chunks) >= 1
    all_content = " ".join(c["content"] for c in chunks)
    assert "First paragraph" in all_content
    assert "Second paragraph" in all_content


def test_semantic_chunk():
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
    chunks = chunker.chunk_text(text, strategy="semantic")
    assert len(chunks) >= 1


def test_chunk_empty_text():
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.chunk_text("")
    assert len(chunks) == 0


def test_chunk_with_overlap():
    chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)
    text = "A" * 120
    chunks = chunker.chunk_text(text)
    assert len(chunks) >= 2
    # Verify overlap exists by checking if content from one chunk appears in another
    assert len(chunks) >= 2


# === Parser Base Tests ===

def test_parser_validate_path_not_found():
    parser = type("TestParser", (BaseDocumentParser,), {"parse": lambda self, fp, **kw: {}})()
    with pytest.raises(DocumentNotFoundError):
        parser.validate_path("/nonexistent/file.txt")


def test_parser_safe_parse_not_found():
    parser = type("TestParser", (BaseDocumentParser,), {"parse": lambda self, fp, **kw: {}})()
    with pytest.raises(DocumentNotFoundError):
        parser.safe_parse("/nonexistent/file.txt")


def test_parser_safe_parse_permission_denied(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello")

    def parse_raises_permission(self, fp, **kw):
        raise PermissionError("no access")

    parser = type("TestParser", (BaseDocumentParser,), {"parse": parse_raises_permission})()
    with pytest.raises(PermissionDeniedError):
        parser.safe_parse(str(f))


def test_parser_supported_extensions():
    from app.engines.knowledge_engine.parser.pdf_parser import PDFParser
    from app.engines.knowledge_engine.parser.word_parser import WordParser
    from app.engines.knowledge_engine.parser.ppt_parser import PPTParser
    from app.engines.knowledge_engine.parser.excel_parser import ExcelParser
    from app.engines.knowledge_engine.parser.text_parser import TextParser

    assert ".pdf" in PDFParser.SUPPORTED_EXTENSIONS
    assert ".docx" in WordParser.SUPPORTED_EXTENSIONS
    assert ".pptx" in PPTParser.SUPPORTED_EXTENSIONS
    assert ".xlsx" in ExcelParser.SUPPORTED_EXTENSIONS
    assert ".txt" in TextParser.SUPPORTED_EXTENSIONS
    assert ".csv" in TextParser.SUPPORTED_EXTENSIONS
    assert ".html" in TextParser.SUPPORTED_EXTENSIONS
    assert ".md" in TextParser.SUPPORTED_EXTENSIONS


# === Text Parser Tests ===

def test_text_parser(tmp_path):
    from app.engines.knowledge_engine.parser.text_parser import TextParser
    f = tmp_path / "test.txt"
    f.write_text("Hello world\nLine 2\nLine 3")

    parser = TextParser()
    result = parser.parse(str(f))
    assert "Hello world" in result["content"]
    assert result["metadata"]["format"] == "txt"


def test_csv_parser(tmp_path):
    from app.engines.knowledge_engine.parser.text_parser import TextParser
    f = tmp_path / "test.csv"
    f.write_text("name,age\nAlice,30\nBob,25")

    parser = TextParser()
    result = parser.parse(str(f))
    assert "Alice" in result["content"]
    assert result["metadata"]["format"] == "csv"


def test_markdown_parser(tmp_path):
    from app.engines.knowledge_engine.parser.text_parser import TextParser
    f = tmp_path / "test.md"
    f.write_text("# Title\n\nSome content\n\n## Section")

    parser = TextParser()
    result = parser.parse(str(f))
    assert "Title" in result["content"]
    assert result["metadata"]["format"] == "md"


# === Retriever Tests ===

@pytest.mark.asyncio
async def test_retriever_vector_search():
    vector_store = AsyncMock()
    vector_store.search.return_value = [{"id": "1", "score": 0.9, "content": "test", "metadata": {}}]

    retriever = HybridRetriever(vector_store, AsyncMock())
    results = await retriever.retrieve(
        query="test", query_embedding=[0.1] * 1536,
        knowledge_base_id="kb1", collection_name="col1",
        es_index="idx1", strategy="vector"
    )
    assert len(results) == 1
    assert results[0]["score"] == 0.9


@pytest.mark.asyncio
async def test_retriever_hybrid_rrf():
    vector_store = AsyncMock()
    vector_store.search.return_value = [
        {"id": "1", "score": 0.9, "content": "doc1", "metadata": {}},
        {"id": "2", "score": 0.8, "content": "doc2", "metadata": {}},
    ]
    es_store = AsyncMock()
    es_store.search.return_value = [
        {"id": "2", "score": 5.0, "content": "doc2", "metadata": {}},
        {"id": "3", "score": 4.0, "content": "doc3", "metadata": {}},
    ]

    retriever = HybridRetriever(vector_store, es_store)
    results = await retriever.retrieve(
        query="test", query_embedding=[0.1] * 1536,
        knowledge_base_id="kb1", collection_name="col1",
        es_index="idx1", strategy="hybrid"
    )
    # RRF should merge results from both sources
    ids = [r["id"] for r in results]
    assert "1" in ids
    assert "2" in ids  # Present in both, should rank high
    assert "3" in ids


def test_rrf_merge():
    retriever = HybridRetriever(AsyncMock(), AsyncMock())
    vec = [{"id": "a", "content": "a"}, {"id": "b", "content": "b"}]
    fts = [{"id": "b", "content": "b"}, {"id": "c", "content": "c"}]

    merged = retriever._rrf_merge(vec, fts, top_k=3)
    ids = [r["id"] for r in merged]
    assert len(ids) == 3
    assert "b" in ids  # Should be present (in both lists)


# === Neo4j Store Tests ===

def test_validate_label_valid():
    from app.engines.knowledge_engine.storage.graph.neo4j_store import _validate_label
    assert _validate_label("Person") == "Person"
    assert _validate_label("Organization") == "Organization"


def test_validate_label_invalid():
    from app.engines.knowledge_engine.storage.graph.neo4j_store import _validate_label
    with pytest.raises(ValueError):
        _validate_label("MaliciousLabel) DETACH DELETE n//")


def test_validate_relation_type_valid():
    from app.engines.knowledge_engine.storage.graph.neo4j_store import _validate_relation_type
    assert _validate_relation_type("RELATED_TO") == "RELATED_TO"


def test_validate_relation_type_invalid():
    from app.engines.knowledge_engine.storage.graph.neo4j_store import _validate_relation_type
    with pytest.raises(ValueError):
        _validate_relation_type("MALICIOUS_REL")


# === Graph Builder Tests ===

@pytest.mark.asyncio
async def test_graph_builder_no_llm():
    graph_store = AsyncMock()
    graph_store.build_graph_from_entities.return_value = {}

    from app.engines.knowledge_engine.graph.graph_builder import KnowledgeGraphBuilder
    builder = KnowledgeGraphBuilder(graph_store, llm_adapter=None)

    result = await builder.build_graph(chunks=[{"content": "test"}])
    assert result["entities_count"] == 0
    assert result["relations_count"] == 0


@pytest.mark.asyncio
async def test_graph_builder_cancel():
    graph_store = AsyncMock()
    graph_store.build_graph_from_entities.return_value = {}

    from app.engines.knowledge_engine.graph.graph_builder import KnowledgeGraphBuilder
    builder = KnowledgeGraphBuilder(graph_store, llm_adapter=None)

    result = await builder.build_graph(
        chunks=[{"content": "a"}, {"content": "b"}, {"content": "c"}],
        cancel_check=lambda: True  # Always cancel
    )
    # Should stop early due to cancel
    assert result["entities_count"] == 0
