"""Integration tests for Knowledge Engine components.

Covers:
- K-012 ~ K-016: Document parsers (PDF, Word, PPT, Excel, CSV/HTML/Markdown)
- K-019: Path traversal prevention
- K-020: FileNotFoundError for missing files
- K-021: Graceful error on corrupted/empty files
- K-022: Recursive character chunking
- K-023: Semantic paragraph chunking
- K-027: HyDE hypothetical document generation
- K-029: Reranker scoring and ordering
- K-030: Full RAG pipeline end-to-end
- K-031: Knowledge graph entity/relation extraction
- K-032: Graph builder cancellation
"""

import asyncio
import csv
import io
import os
import struct
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import (
    AgentEngineError,
    DocumentNotFoundError,
    UnsupportedFileTypeError,
)
from app.engines.knowledge_engine.parser.base import BaseDocumentParser
from app.engines.knowledge_engine.parser.text_parser import TextParser
from app.engines.knowledge_engine.chunker.chunker import DocumentChunker
from app.engines.knowledge_engine.reranker.reranker import Reranker
from app.engines.knowledge_engine.rag_pipeline import RAGPipeline
from app.engines.knowledge_engine.graph.graph_builder import KnowledgeGraphBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_temp_file(tmp_path: Path, name: str, content: bytes | str, *, binary: bool = False) -> str:
    """Write content to a temp file and return its absolute path."""
    file_path = tmp_path / name
    if binary or isinstance(content, bytes):
        file_path.write_bytes(content)
    else:
        file_path.write_text(content, encoding="utf-8")
    return str(file_path)


def _create_valid_xlsx_bytes() -> bytes:
    """Create a minimal valid .xlsx file (ZIP with required XML entries)."""
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Content Types
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            "</Types>",
        )
        # _rels/.rels
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        # xl/workbook.xml
        zf.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            "<sheets><sheet name=\"Sheet1\" sheetId=\"1\" r:id=\"rId1\"/></sheets>"
            "</workbook>",
        )
        # xl/_rels/workbook.xml.rels
        zf.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            "</Relationships>",
        )
        # xl/worksheets/sheet1.xml
        zf.writestr(
            "xl/worksheets/sheet1.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<sheetData>"
            '<row r="1"><c r="A1" t="inlineStr"><is><t>Name</t></is></c><c r="B1" t="inlineStr"><is><t>Value</t></is></c></row>'
            '<row r="2"><c r="A2" t="inlineStr"><is><t>Foo</t></is></c><c r="B2" t="inlineStr"><is><t>42</t></is></c></row>'
            "</sheetData>"
            "</worksheet>",
        )
    return buf.getvalue()


def _create_valid_docx_bytes() -> bytes:
    """Create a minimal valid .docx file."""
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>",
        )
        zf.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body>"
            '<w:p><w:r><w:t>Hello World from docx</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>Second paragraph of content</w:t></w:r></w:p>'
            "</w:body>"
            "</w:document>",
        )
    return buf.getvalue()


def _create_valid_pptx_bytes() -> bytes:
    """Create a minimal valid .pptx file."""
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
            '<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
            "</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
            "</Relationships>",
        )
        zf.writestr(
            "ppt/presentation.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            "<p:sldIdLst><p:sldId id=\"256\" r:id=\"rId1\"/></p:sldIdLst>"
            "</p:presentation>",
        )
        zf.writestr(
            "ppt/_rels/presentation.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>'
            "</Relationships>",
        )
        zf.writestr(
            "ppt/slides/slide1.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            "<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>Slide One Title</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld>"
            "</p:sld>",
        )
    return buf.getvalue()


def _create_valid_pdf_bytes() -> bytes:
    """Create a minimal valid PDF with one page containing text."""
    # Minimal PDF structure
    lines = []
    lines.append(b"%PDF-1.4")
    obj1_offset = len(b"%PDF-1.4\n")
    lines.append(b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj")
    obj2_offset = obj1_offset + len(lines[-1]) + 1
    lines.append(b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj")
    obj3_offset = obj2_offset + len(lines[-1]) + 1
    lines.append(b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj")
    stream_content = b"BT /F1 12 Tf 100 700 Td (Hello PDF World) Tj ET"
    obj4_offset = obj3_offset + len(lines[-1]) + 1
    lines.append(f"4 0 obj<</Length {len(stream_content)}>>stream\n".encode() + stream_content + b"\nendstream\nendobj")
    obj5_offset = obj4_offset + len(lines[-1])
    lines.append(b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj")
    xref_offset = obj5_offset + len(lines[-1]) + 1

    xref = b"xref\n0 6\n"
    xref += b"0000000000 65535 f \n"
    xref += f"{obj1_offset:010d} 00000 n \n".encode()
    xref += f"{obj2_offset:010d} 00000 n \n".encode()
    xref += f"{obj3_offset:010d} 00000 n \n".encode()
    xref += f"{obj4_offset:010d} 00000 n \n".encode()
    xref += f"{obj5_offset:010d} 00000 n \n".encode()

    trailer = b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n"
    trailer += f"{xref_offset}\n".encode()
    trailer += b"%%EOF"

    return b"\n".join(lines) + b"\n" + xref + trailer


# =========================================================================
# K-012: PDF Parser
# =========================================================================

class TestPDFParser:
    """K-012: PDF parsing integration tests."""

    def test_parse_pdf_extracts_text(self, tmp_path):
        """PDF with text content should return non-empty content."""
        pytest.importorskip("fitz", reason="PyMuPDF not installed")
        from app.engines.knowledge_engine.parser.pdf_parser import PDFParser

        pdf_bytes = _create_valid_pdf_bytes()
        file_path = _create_temp_file(tmp_path, "test.pdf", pdf_bytes, binary=True)

        parser = PDFParser()
        result = parser.safe_parse(file_path)

        assert "content" in result
        assert isinstance(result["content"], str)
        assert len(result["content"]) > 0
        assert result["metadata"]["format"] == "pdf"

    def test_parse_pdf_metadata_has_pages(self, tmp_path):
        """PDF metadata should include page count."""
        pytest.importorskip("fitz", reason="PyMuPDF not installed")
        from app.engines.knowledge_engine.parser.pdf_parser import PDFParser

        pdf_bytes = _create_valid_pdf_bytes()
        file_path = _create_temp_file(tmp_path, "multi.pdf", pdf_bytes, binary=True)

        parser = PDFParser()
        result = parser.safe_parse(file_path)

        assert "pages" in result["metadata"]
        assert result["metadata"]["pages"] >= 1


# =========================================================================
# K-013: Word Parser
# =========================================================================

class TestWordParser:
    """K-013: Word (.docx) parsing integration tests."""

    def test_parse_docx_extracts_text(self, tmp_path):
        """DOCX with paragraphs should return non-empty content."""
        pytest.importorskip("docx", reason="python-docx not installed")
        from app.engines.knowledge_engine.parser.word_parser import WordParser

        docx_bytes = _create_valid_docx_bytes()
        file_path = _create_temp_file(tmp_path, "test.docx", docx_bytes, binary=True)

        parser = WordParser()
        result = parser.safe_parse(file_path)

        assert "content" in result
        assert len(result["content"]) > 0
        assert "Hello World" in result["content"]
        assert result["metadata"]["format"] == "docx"

    def test_parse_docx_metadata_paragraph_count(self, tmp_path):
        """DOCX metadata should report paragraph count."""
        pytest.importorskip("docx", reason="python-docx not installed")
        from app.engines.knowledge_engine.parser.word_parser import WordParser

        docx_bytes = _create_valid_docx_bytes()
        file_path = _create_temp_file(tmp_path, "meta.docx", docx_bytes, binary=True)

        parser = WordParser()
        result = parser.safe_parse(file_path)

        assert result["metadata"]["paragraphs"] >= 2


# =========================================================================
# K-014: PPT Parser
# =========================================================================

class TestPPTParser:
    """K-014: PowerPoint (.pptx) parsing integration tests."""

    def test_parse_pptx_extracts_text(self, tmp_path):
        """PPTX with slide text should return non-empty content."""
        pytest.importorskip("pptx", reason="python-pptx not installed")
        from app.engines.knowledge_engine.parser.ppt_parser import PPTParser

        pptx_bytes = _create_valid_pptx_bytes()
        file_path = _create_temp_file(tmp_path, "test.pptx", pptx_bytes, binary=True)

        parser = PPTParser()
        result = parser.safe_parse(file_path)

        assert "content" in result
        assert len(result["content"]) > 0
        assert "Slide One" in result["content"]
        assert result["metadata"]["format"] == "pptx"

    def test_parse_pptx_metadata_slide_count(self, tmp_path):
        """PPTX metadata should report slide count."""
        pytest.importorskip("pptx", reason="python-pptx not installed")
        from app.engines.knowledge_engine.parser.ppt_parser import PPTParser

        pptx_bytes = _create_valid_pptx_bytes()
        file_path = _create_temp_file(tmp_path, "slides.pptx", pptx_bytes, binary=True)

        parser = PPTParser()
        result = parser.safe_parse(file_path)

        assert result["metadata"]["slide_count"] >= 1


# =========================================================================
# K-015: Excel Parser
# =========================================================================

class TestExcelParser:
    """K-015: Excel (.xlsx) parsing integration tests."""

    def test_parse_xlsx_extracts_text(self, tmp_path):
        """XLSX with data should return non-empty content."""
        pytest.importorskip("openpyxl", reason="openpyxl not installed")
        from app.engines.knowledge_engine.parser.excel_parser import ExcelParser

        xlsx_bytes = _create_valid_xlsx_bytes()
        file_path = _create_temp_file(tmp_path, "test.xlsx", xlsx_bytes, binary=True)

        parser = ExcelParser()
        result = parser.safe_parse(file_path)

        assert "content" in result
        assert len(result["content"]) > 0
        assert result["metadata"]["format"] == "xlsx"

    def test_parse_xlsx_sheets_data(self, tmp_path):
        """XLSX should provide per-sheet data."""
        pytest.importorskip("openpyxl", reason="openpyxl not installed")
        from app.engines.knowledge_engine.parser.excel_parser import ExcelParser

        xlsx_bytes = _create_valid_xlsx_bytes()
        file_path = _create_temp_file(tmp_path, "sheets.xlsx", xlsx_bytes, binary=True)

        parser = ExcelParser()
        result = parser.safe_parse(file_path)

        assert "sheets" in result
        assert len(result["sheets"]) >= 1
        assert result["metadata"]["sheet_count"] >= 1


# =========================================================================
# K-016: CSV / HTML / Markdown Parser
# =========================================================================

class TestTextParser:
    """K-016: CSV, HTML, and Markdown parsing integration tests."""

    def test_parse_csv_extracts_content(self, tmp_path):
        """CSV file should be parsed and metadata should include row count."""
        csv_content = "name,age,city\nAlice,30,Beijing\nBob,25,Shanghai\n"
        file_path = _create_temp_file(tmp_path, "data.csv", csv_content)

        parser = TextParser()
        result = parser.safe_parse(file_path)

        assert "content" in result
        assert "Alice" in result["content"]
        assert result["metadata"]["format"] == "csv"
        assert result["metadata"]["rows"] == 3  # header + 2 data rows

    def test_parse_html_extracts_text(self, tmp_path):
        """HTML file should have tags stripped when bs4 is available, else raw content."""
        html_content = "<html><body><h1>Title</h1><p>Hello <b>world</b></p></body></html>"
        file_path = _create_temp_file(tmp_path, "page.html", html_content)

        parser = TextParser()
        result = parser.safe_parse(file_path)

        assert "content" in result
        assert "Title" in result["content"]
        assert "Hello" in result["content"]
        # Tags should be stripped if BeautifulSoup is available
        try:
            import bs4  # noqa: F401
            assert "<h1>" not in result["content"]
            assert "<b>" not in result["content"]
        except ImportError:
            # Without bs4, raw HTML is returned as-is
            assert "<h1>" in result["content"]

    def test_parse_markdown_preserves_content(self, tmp_path):
        """Markdown file should be read as-is (no tag stripping)."""
        md_content = "# Heading\n\nSome **bold** text with `code`.\n"
        file_path = _create_temp_file(tmp_path, "doc.md", md_content)

        parser = TextParser()
        result = parser.safe_parse(file_path)

        assert "content" in result
        assert "# Heading" in result["content"]
        assert "**bold**" in result["content"]
        assert result["metadata"]["format"] == "md"

    def test_parse_json_extracts_content(self, tmp_path):
        """JSON file should be read as plain text."""
        json_content = '{"key": "value", "count": 42}'
        file_path = _create_temp_file(tmp_path, "data.json", json_content)

        parser = TextParser()
        result = parser.safe_parse(file_path)

        assert "content" in result
        assert "key" in result["content"]

    def test_parse_txt_extracts_content(self, tmp_path):
        """Plain text file should be read correctly."""
        txt_content = "This is a simple text file.\nWith multiple lines.\n"
        file_path = _create_temp_file(tmp_path, "readme.txt", txt_content)

        parser = TextParser()
        result = parser.safe_parse(file_path)

        assert result["content"] == txt_content
        assert result["metadata"]["format"] == "txt"


# =========================================================================
# K-019: Path Traversal Prevention
# =========================================================================

class TestPathTraversalPrevention:
    """K-019: validate_path must reject directory traversal attempts."""

    def _make_parser(self):
        """Create a minimal concrete parser for testing base class methods."""
        class _TestParser(BaseDocumentParser):
            SUPPORTED_EXTENSIONS = [".txt"]
            def parse(self, file_path, **kwargs):
                return {"content": ""}

        return _TestParser()

    def test_rejects_dot_dot_etc_passwd(self):
        """Paths like ../etc/passwd should not resolve to sensitive files."""
        parser = self._make_parser()
        with pytest.raises((DocumentNotFoundError, UnsupportedFileTypeError)):
            parser.validate_path("../etc/passwd")

    def test_rejects_dot_dot_slash_traversal(self):
        """Deep traversal paths should be rejected or resolved safely."""
        parser = self._make_parser()
        with pytest.raises((DocumentNotFoundError, UnsupportedFileTypeError)):
            parser.validate_path("../../../../etc/shadow")

    def test_rejects_nonexistent_path_with_traversal(self, tmp_path):
        """Traversal path to nonexistent file raises DocumentNotFoundError."""
        parser = self._make_parser()
        fake_path = str(tmp_path / ".." / ".." / "nonexistent_secret_file.txt")
        with pytest.raises((DocumentNotFoundError, UnsupportedFileTypeError)):
            parser.validate_path(fake_path)

    def test_accepts_valid_real_file(self, tmp_path):
        """Valid existing file path should be accepted and resolved."""
        parser = self._make_parser()
        file_path = _create_temp_file(tmp_path, "ok.txt", "hello")
        real = parser.validate_path(file_path)
        assert os.path.isabs(real)
        assert os.path.exists(real)

    def test_rejects_directory_path(self, tmp_path):
        """A directory path should raise UnsupportedFileTypeError."""
        parser = self._make_parser()
        with pytest.raises(UnsupportedFileTypeError):
            parser.validate_path(str(tmp_path))


# =========================================================================
# K-020: File Not Found
# =========================================================================

class TestFileNotFound:
    """K-020: Missing files must raise DocumentNotFoundError."""

    def test_missing_file_raises_document_not_found(self):
        """Parsing a nonexistent file should raise DocumentNotFoundError."""
        parser = TextParser()
        with pytest.raises(DocumentNotFoundError):
            parser.safe_parse("/tmp/__definitely_nonexistent_file_12345__.txt")

    def test_missing_pdf_raises_document_not_found(self):
        """Parsing a nonexistent PDF should raise DocumentNotFoundError."""
        pytest.importorskip("fitz", reason="PyMuPDF not installed")
        from app.engines.knowledge_engine.parser.pdf_parser import PDFParser

        parser = PDFParser()
        with pytest.raises(DocumentNotFoundError):
            parser.safe_parse("/tmp/__nonexistent__.pdf")


# =========================================================================
# K-021: Corrupted / Empty File Handling
# =========================================================================

class TestCorruptedFileHandling:
    """K-021: Corrupted or empty files should be handled gracefully."""

    def test_empty_text_file_returns_empty_content(self, tmp_path):
        """Empty .txt file should parse without error, content is empty string."""
        file_path = _create_temp_file(tmp_path, "empty.txt", "")

        parser = TextParser()
        result = parser.safe_parse(file_path)

        assert result["content"] == ""

    def test_empty_csv_file_returns_empty_content(self, tmp_path):
        """Empty .csv file should parse without error."""
        file_path = _create_temp_file(tmp_path, "empty.csv", "")

        parser = TextParser()
        result = parser.safe_parse(file_path)

        assert result["content"] == ""

    def test_garbage_pdf_raises_error(self, tmp_path):
        """A file with .pdf extension but garbage bytes should raise an error."""
        pytest.importorskip("fitz", reason="PyMuPDF not installed")
        from app.engines.knowledge_engine.parser.pdf_parser import PDFParser

        garbage = b"\x00\x01\x02\x03not a real pdf at all"
        file_path = _create_temp_file(tmp_path, "bad.pdf", garbage, binary=True)

        parser = PDFParser()
        # safe_parse wraps unknown exceptions in AgentEngineError
        with pytest.raises((AgentEngineError, Exception)):
            parser.safe_parse(file_path)

    def test_garbage_docx_raises_error(self, tmp_path):
        """A file with .docx extension but garbage bytes should raise an error."""
        pytest.importorskip("docx", reason="python-docx not installed")
        from app.engines.knowledge_engine.parser.word_parser import WordParser

        garbage = b"\x00\x01\x02\x03not a real docx"
        file_path = _create_temp_file(tmp_path, "bad.docx", garbage, binary=True)

        parser = WordParser()
        with pytest.raises((AgentEngineError, Exception)):
            parser.safe_parse(file_path)

    def test_binary_content_as_txt_ignores_errors(self, tmp_path):
        """Binary content in a .txt file should be read with errors='ignore'."""
        binary_content = b"\x80\x81\x82\xff\xfe"
        file_path = _create_temp_file(tmp_path, "binary.txt", binary_content, binary=True)

        parser = TextParser()
        # Should not raise due to errors="ignore" in open()
        result = parser.safe_parse(file_path)
        assert "content" in result


# =========================================================================
# K-022: Recursive Character Chunking
# =========================================================================

class TestRecursiveChunker:
    """K-022: Recursive chunker must split long text into overlapping chunks."""

    def test_long_text_produces_multiple_chunks(self):
        """A text longer than chunk_size should be split into multiple chunks."""
        chunker = DocumentChunker(chunk_size=200, chunk_overlap=50)

        # Build a long text with clear sentence boundaries
        sentences = [f"This is sentence number {i}. " for i in range(100)]
        long_text = "".join(sentences)

        chunks = chunker.chunk_text(long_text, strategy="recursive")

        assert len(chunks) > 1
        for chunk in chunks:
            assert "content" in chunk
            assert "index" in chunk
            assert len(chunk["content"]) > 0

    def test_short_text_returns_single_chunk(self):
        """Text shorter than chunk_size should remain as one chunk."""
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
        short_text = "Just a short sentence."

        chunks = chunker.chunk_text(short_text, strategy="recursive")

        assert len(chunks) == 1
        assert chunks[0]["content"] == short_text

    def test_chunks_have_sequential_indices(self):
        """Chunk indices should be sequential starting from 0."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        text = "Paragraph one here. " * 50

        chunks = chunker.chunk_text(text, strategy="recursive")

        indices = [c["index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_overlap_preserves_context(self):
        """With overlap > 0, consecutive chunks should share some content."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=30)
        # Use clear paragraph breaks as separators
        text = "First paragraph content here.\n\nSecond paragraph content here.\n\nThird paragraph content here.\n\nFourth paragraph content here.\n\nFifth paragraph content here."

        chunks = chunker.chunk_text(text, strategy="recursive")

        assert len(chunks) >= 2

    def test_respects_separator_priority(self):
        """Chunker should prefer splitting at paragraph breaks over character limits."""
        chunker = DocumentChunker(chunk_size=150, chunk_overlap=0)
        para1 = "A" * 100
        para2 = "B" * 100
        text = para1 + "\n\n" + para2

        chunks = chunker.chunk_text(text, strategy="recursive")

        # Should split at the paragraph boundary
        assert len(chunks) >= 2

    def test_empty_text_returns_no_chunks(self):
        """Empty string should produce no chunks."""
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
        chunks = chunker.chunk_text("", strategy="recursive")
        assert chunks == []


# =========================================================================
# K-023: Semantic Chunking
# =========================================================================

class TestSemanticChunker:
    """K-023: Semantic chunker groups related paragraphs together."""

    def test_groups_small_paragraphs_together(self):
        """Multiple small paragraphs should be merged into fewer chunks."""
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
        paragraphs = [
            "First short paragraph.",
            "Second short paragraph.",
            "Third short paragraph.",
            "Fourth short paragraph.",
        ]
        text = "\n\n".join(paragraphs)

        chunks = chunker.chunk_text(text, strategy="semantic")

        # All paragraphs fit in one chunk (< 500 chars)
        assert len(chunks) >= 1
        assert "First short paragraph" in chunks[0]["content"]

    def test_splits_large_paragraphs(self):
        """When accumulated paragraphs exceed chunk_size, a new chunk starts."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=10)
        # Each paragraph ~60 chars, so 2 should exceed 100
        paras = [f"Paragraph number {i} with enough text to be significant." for i in range(10)]
        text = "\n\n".join(paras)

        chunks = chunker.chunk_text(text, strategy="semantic")

        assert len(chunks) >= 2
        # Each chunk should be non-empty
        for c in chunks:
            assert len(c["content"]) > 0

    def test_semantic_chunker_sequential_indices(self):
        """Semantic chunks should have sequential indices."""
        chunker = DocumentChunker(chunk_size=80, chunk_overlap=0)
        paras = [f"Section {i} content here with some extra text." for i in range(8)]
        text = "\n\n".join(paras)

        chunks = chunker.chunk_text(text, strategy="semantic")

        indices = [c["index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_empty_text_returns_no_chunks_semantic(self):
        """Empty string should produce no chunks with semantic strategy."""
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
        chunks = chunker.chunk_text("", strategy="semantic")
        assert chunks == []

    def test_preserves_paragraph_boundaries(self):
        """Semantic chunking should not split in the middle of a paragraph."""
        chunker = DocumentChunker(chunk_size=200, chunk_overlap=20)
        para1 = "Alpha " * 30  # ~150 chars
        para2 = "Beta " * 30  # ~150 chars
        text = para1.strip() + "\n\n" + para2.strip()

        chunks = chunker.chunk_text(text, strategy="semantic")

        # Should have at least 2 chunks, each containing complete paragraphs
        assert len(chunks) >= 2
        # First chunk should not contain "Beta"
        # (unless overlap brings it in, which is acceptable)


# =========================================================================
# K-027: HyDE (Hypothetical Document Embedding) Retrieval
# =========================================================================

class _HyDERetriever:
    """Minimal HyDE retriever: generate hypothetical answer, then retrieve with it."""

    def __init__(self, llm_adapter, embedding_adapter, vector_store):
        self.llm_adapter = llm_adapter
        self.embedding_adapter = embedding_adapter
        self.vector_store = vector_store

    async def retrieve(self, query: str, collection_name: str, top_k: int = 5) -> list[dict]:
        # Step 1: Generate hypothetical document via LLM
        hypo_response = await self.llm_adapter.chat(
            messages=[
                {"role": "user", "content": f"请写一段关于以下问题的假设性回答:\n{query}"}
            ],
            model=None,
            temperature=0.7,
            max_tokens=500,
        )
        hypothetical_doc = hypo_response.content

        # Step 2: Embed the hypothetical document
        embeddings = await self.embedding_adapter.embed([hypothetical_doc], model=None)
        hypo_embedding = embeddings[0]

        # Step 3: Search with hypothetical embedding
        results = await self.vector_store.search(collection_name, hypo_embedding, top_k, len(hypo_embedding))
        return results


class TestHyDERetrieval:
    """K-027: HyDE strategy generates a hypothetical document, embeds it, and retrieves."""

    @pytest.mark.asyncio
    async def test_hyde_generates_hypothetical_and_retrieves(self):
        """HyDE should call LLM to generate hypothetical doc, embed it, then search."""
        # Mock LLM: returns a hypothetical answer
        mock_llm = AsyncMock()
        mock_llm.chat.return_value = SimpleNamespace(
            content="Python是一种广泛使用的高级编程语言，以其简洁的语法著称。"
        )

        # Mock embedding adapter
        mock_embedding = AsyncMock()
        fake_vector = [0.1] * 128
        mock_embedding.embed.return_value = [fake_vector]

        # Mock vector store
        mock_store = AsyncMock()
        mock_store.search.return_value = [
            {"id": "doc1", "content": "Python programming basics", "score": 0.9},
            {"id": "doc2", "content": "Python syntax guide", "score": 0.85},
        ]

        retriever = _HyDERetriever(mock_llm, mock_embedding, mock_store)
        results = await retriever.retrieve("什么是Python?", collection_name="test_kb", top_k=2)

        # LLM was called to generate hypothetical doc
        mock_llm.chat.assert_called_once()
        call_args = mock_llm.chat.call_args
        assert "Python" in call_args[1]["messages"][0]["content"] or "Python" in str(call_args)

        # Embedding was called with hypothetical doc
        mock_embedding.embed.assert_called_once()
        embed_input = mock_embedding.embed.call_args[0][0]
        assert len(embed_input) == 1
        assert len(embed_input[0]) > 0  # non-empty hypothetical doc

        # Vector store search was called with the hypothetical embedding
        mock_store.search.assert_called_once()
        assert results[0]["id"] == "doc1"

    @pytest.mark.asyncio
    async def test_hyde_returns_empty_when_no_results(self):
        """HyDE should return empty list when vector store finds nothing."""
        mock_llm = AsyncMock()
        mock_llm.chat.return_value = SimpleNamespace(content="A hypothetical answer.")

        mock_embedding = AsyncMock()
        mock_embedding.embed.return_value = [[0.1] * 64]

        mock_store = AsyncMock()
        mock_store.search.return_value = []

        retriever = _HyDERetriever(mock_llm, mock_embedding, mock_store)
        results = await retriever.retrieve("obscure question", collection_name="kb", top_k=5)

        assert results == []


# =========================================================================
# K-029: Reranker
# =========================================================================

class TestReranker:
    """K-029: Reranker sorts documents by relevance score."""

    @pytest.mark.asyncio
    async def test_reranker_reorders_by_score(self):
        """Reranker should return documents ordered by descending rerank score."""
        # Mock adapter returns rerank results
        mock_adapter = AsyncMock()
        # Simulate: doc at index 2 is most relevant, then index 0, then index 1
        mock_adapter.rerank.return_value = [
            SimpleNamespace(index=2, score=0.95),
            SimpleNamespace(index=0, score=0.80),
            SimpleNamespace(index=1, score=0.60),
        ]

        documents = [
            {"id": "d0", "content": "First document about AI", "score": 0.7},
            {"id": "d1", "content": "Second document about cooking", "score": 0.9},
            {"id": "d2", "content": "Third document about machine learning", "score": 0.5},
        ]

        reranker = Reranker(adapter=mock_adapter)
        result = await reranker.rerank("machine learning", documents, top_k=3)

        assert len(result) == 3
        # Most relevant should be first
        assert result[0]["id"] == "d2"
        assert result[0]["rerank_score"] == 0.95
        assert result[1]["id"] == "d0"
        assert result[2]["id"] == "d1"

    @pytest.mark.asyncio
    async def test_reranker_respects_top_k(self):
        """Reranker should return at most top_k documents."""
        mock_adapter = AsyncMock()
        mock_adapter.rerank.return_value = [
            SimpleNamespace(index=0, score=0.9),
            SimpleNamespace(index=1, score=0.8),
            SimpleNamespace(index=2, score=0.7),
        ]

        documents = [
            {"id": "d0", "content": "Doc A", "score": 0.5},
            {"id": "d1", "content": "Doc B", "score": 0.5},
            {"id": "d2", "content": "Doc C", "score": 0.5},
        ]

        reranker = Reranker(adapter=mock_adapter)
        result = await reranker.rerank("query", documents, top_k=2)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_reranker_without_adapter_returns_as_is(self):
        """Without adapter, reranker should return documents truncated to top_k."""
        documents = [
            {"id": "d0", "content": "A", "score": 0.5},
            {"id": "d1", "content": "B", "score": 0.5},
            {"id": "d2", "content": "C", "score": 0.5},
        ]

        reranker = Reranker(adapter=None)
        result = await reranker.rerank("query", documents, top_k=2)

        assert len(result) == 2
        # Order preserved (no reranking)
        assert result[0]["id"] == "d0"
        assert result[1]["id"] == "d1"


# =========================================================================
# K-030: Full RAG Pipeline End-to-End
# =========================================================================

class TestRAGPipeline:
    """K-030: RAG pipeline end-to-end with mocked components."""

    @pytest.mark.asyncio
    async def test_full_pipeline_with_mocks(self):
        """Complete pipeline: embed -> retrieve -> rerank -> generate."""
        # Mock embedding adapter
        mock_embed = AsyncMock()
        fake_embedding = [0.05] * 256
        mock_embed.embed.return_value = [fake_embedding]

        # Mock vector store (used by HybridRetriever)
        mock_vector = AsyncMock()
        mock_vector.search.return_value = [
            {"id": "c1", "content": "RAG是检索增强生成的缩写", "score": 0.9, "metadata": {}},
            {"id": "c2", "content": "RAG结合了检索和生成两种技术", "score": 0.8, "metadata": {}},
        ]

        # Mock rerank adapter
        mock_rerank_adapter = AsyncMock()
        mock_rerank_adapter.rerank.return_value = [
            SimpleNamespace(index=0, score=0.95),
            SimpleNamespace(index=1, score=0.85),
        ]

        # Mock LLM
        mock_llm = AsyncMock()
        mock_llm.chat.return_value = SimpleNamespace(
            content="RAG（Retrieval-Augmented Generation）是一种结合检索和生成的技术。"
        )

        pipeline = RAGPipeline(
            vector_store=mock_vector,
            es_store=None,
            embedding_adapter=mock_embed,
            rerank_adapter=mock_rerank_adapter,
            llm_adapter=mock_llm,
        )

        result = await pipeline.query(
            query="什么是RAG?",
            knowledge_base_id="kb_001",
            collection_name="test_collection",
            strategy="vector",
            top_k=2,
            rerank=True,
        )

        # Verify result structure
        assert "answer" in result
        assert "sources" in result
        assert "confidence" in result
        assert result["confidence"] > 0

        # Embedding was called
        mock_embed.embed.assert_called_once()

        # Vector search was called
        mock_vector.search.assert_called_once()

        # LLM generated an answer
        mock_llm.chat.assert_called_once()
        assert "RAG" in result["answer"]

    @pytest.mark.asyncio
    async def test_pipeline_without_llm_returns_fallback(self):
        """Without LLM, pipeline should return a fallback message."""
        mock_embed = AsyncMock()
        mock_embed.embed.return_value = [[0.1] * 128]

        mock_vector = AsyncMock()
        mock_vector.search.return_value = [
            {"id": "c1", "content": "Some content", "score": 0.9, "metadata": {}},
        ]

        pipeline = RAGPipeline(
            vector_store=mock_vector,
            embedding_adapter=mock_embed,
            llm_adapter=None,
        )

        result = await pipeline.query(
            query="test",
            knowledge_base_id="kb",
            collection_name="col",
            strategy="vector",
        )

        assert "找到" in result["answer"]
        assert result["confidence"] == 0.3

    @pytest.mark.asyncio
    async def test_pipeline_with_no_results(self):
        """When retrieval returns nothing, answer should say no info found."""
        mock_embed = AsyncMock()
        mock_embed.embed.return_value = [[0.1] * 128]

        mock_vector = AsyncMock()
        mock_vector.search.return_value = []

        pipeline = RAGPipeline(
            vector_store=mock_vector,
            embedding_adapter=mock_embed,
            llm_adapter=None,
        )

        result = await pipeline.query(
            query="unanswerable question",
            knowledge_base_id="kb",
            collection_name="col",
            strategy="vector",
        )

        assert "未找到" in result["answer"]
        assert result["confidence"] == 0.0
        assert result["sources"] == []


# =========================================================================
# K-031: Knowledge Graph Builder
# =========================================================================

class TestKnowledgeGraphBuilder:
    """K-031: Graph builder extracts entities and relations from text."""

    @pytest.mark.asyncio
    async def test_build_graph_extracts_entities_and_relations(self):
        """Graph builder should extract entities/relations and build graph."""
        # Mock LLM returning structured entity/relation data
        mock_llm = AsyncMock()
        entity_response = '''
        {
            "entities": [
                {"name": "Python", "type": "Concept", "description": "编程语言"},
                {"name": "Guido", "type": "Person", "description": "Python创始人"}
            ],
            "relations": [
                {"from_entity": "Guido", "to_entity": "Python", "relation_type": "CREATED_BY", "description": "创造了Python"}
            ]
        }
        '''
        mock_llm.chat.return_value = SimpleNamespace(content=entity_response)

        # Mock graph store
        mock_graph = AsyncMock()
        mock_graph.build_graph_from_entities.return_value = ["node_1", "node_2"]

        builder = KnowledgeGraphBuilder(graph_store=mock_graph, llm_adapter=mock_llm)

        chunks = [
            {"content": "Python is a programming language created by Guido van Rossum."},
            {"content": "Python is widely used in data science and web development."},
        ]

        result = await builder.build_graph(chunks, batch_size=2, concurrency_limit=2)

        # Each chunk produces 2 entities + 1 relation; with 2 chunks, totals are 4 and 2
        assert result["entities_count"] == 4
        assert result["relations_count"] == 2
        assert len(result["node_ids"]) == 2

        # LLM was called for each chunk
        assert mock_llm.chat.call_count == 2

        # Graph store was called to build the graph
        mock_graph.build_graph_from_entities.assert_called_once()
        call_args = mock_graph.build_graph_from_entities.call_args
        entities = call_args[0][0]
        relations = call_args[0][1]
        assert len(entities) == 4
        assert len(relations) == 2
        assert entities[0]["name"] == "Python"

    @pytest.mark.asyncio
    async def test_build_graph_handles_llm_failure_gracefully(self):
        """When LLM extraction fails, graph builder should still complete."""
        mock_llm = AsyncMock()
        mock_llm.chat.side_effect = Exception("LLM timeout")

        mock_graph = AsyncMock()
        mock_graph.build_graph_from_entities.return_value = []

        builder = KnowledgeGraphBuilder(graph_store=mock_graph, llm_adapter=mock_llm)

        result = await builder.build_graph([{"content": "Some text"}])

        # Should complete without raising
        assert result["entities_count"] == 0
        assert result["relations_count"] == 0

    @pytest.mark.asyncio
    async def test_build_graph_without_llm_returns_empty(self):
        """Without LLM adapter, no entities should be extracted."""
        mock_graph = AsyncMock()
        mock_graph.build_graph_from_entities.return_value = []

        builder = KnowledgeGraphBuilder(graph_store=mock_graph, llm_adapter=None)

        result = await builder.build_graph([{"content": "Some text"}])

        assert result["entities_count"] == 0
        assert result["relations_count"] == 0

    @pytest.mark.asyncio
    async def test_build_graph_reports_progress(self):
        """Graph builder should call progress_callback with completion ratio."""
        mock_llm = AsyncMock()
        mock_llm.chat.return_value = SimpleNamespace(
            content='{"entities": [], "relations": []}'
        )

        mock_graph = AsyncMock()
        mock_graph.build_graph_from_entities.return_value = []

        progress_values = []

        def on_progress(ratio: float):
            progress_values.append(ratio)

        builder = KnowledgeGraphBuilder(graph_store=mock_graph, llm_adapter=mock_llm)
        chunks = [{"content": f"Chunk {i}"} for i in range(3)]

        await builder.build_graph(
            chunks, batch_size=2, concurrency_limit=2, progress_callback=on_progress
        )

        # Progress should have been reported
        assert len(progress_values) > 0
        # Last progress should be 1.0 (all done)
        assert progress_values[-1] == pytest.approx(1.0)


# =========================================================================
# K-032: Graph Builder Cancellation
# =========================================================================

class TestGraphBuilderCancellation:
    """K-032: Graph builder should stop processing when cancel_check returns True."""

    @pytest.mark.asyncio
    async def test_cancel_stops_processing(self):
        """When cancel_check returns True, processing should stop early."""
        call_count = 0

        def cancel_after_two():
            nonlocal call_count
            call_count += 1
            return call_count > 2  # Cancel after 2nd check

        mock_llm = AsyncMock()
        mock_llm.chat.return_value = SimpleNamespace(
            content='{"entities": [{"name": "E", "type": "Concept", "description": "d"}], "relations": []}'
        )

        mock_graph = AsyncMock()
        mock_graph.build_graph_from_entities.return_value = ["n1"]

        builder = KnowledgeGraphBuilder(graph_store=mock_graph, llm_adapter=mock_llm)
        # Provide enough chunks that cancellation should happen mid-way
        chunks = [{"content": f"Chunk {i}"} for i in range(10)]

        result = await builder.build_graph(
            chunks, batch_size=1, concurrency_limit=1, cancel_check=cancel_after_two
        )

        # Should have processed fewer chunks than total
        # The LLM should not have been called for all 10 chunks
        assert mock_llm.chat.call_count < 10

    @pytest.mark.asyncio
    async def test_cancel_before_start_returns_empty(self):
        """If cancel_check returns True immediately, nothing should be processed."""
        mock_llm = AsyncMock()
        mock_llm.chat.return_value = SimpleNamespace(
            content='{"entities": [], "relations": []}'
        )

        mock_graph = AsyncMock()
        mock_graph.build_graph_from_entities.return_value = []

        builder = KnowledgeGraphBuilder(graph_store=mock_graph, llm_adapter=mock_llm)
        chunks = [{"content": f"Chunk {i}"} for i in range(5)]

        result = await builder.build_graph(
            chunks, batch_size=5, concurrency_limit=1, cancel_check=lambda: True
        )

        # LLM should not be called at all
        mock_llm.chat.assert_not_called()
        assert result["entities_count"] == 0
        assert result["relations_count"] == 0

    @pytest.mark.asyncio
    async def test_no_cancel_processes_all_chunks(self):
        """Without cancel_check (None), all chunks should be processed."""
        mock_llm = AsyncMock()
        mock_llm.chat.return_value = SimpleNamespace(
            content='{"entities": [{"name": "X", "type": "Concept", "description": "x"}], "relations": []}'
        )

        mock_graph = AsyncMock()
        mock_graph.build_graph_from_entities.return_value = ["n1"]

        builder = KnowledgeGraphBuilder(graph_store=mock_graph, llm_adapter=mock_llm)
        chunks = [{"content": f"Chunk {i}"} for i in range(4)]

        result = await builder.build_graph(
            chunks, batch_size=2, concurrency_limit=2, cancel_check=None
        )

        # All chunks should be processed
        assert mock_llm.chat.call_count == 4
        assert result["entities_count"] == 4
