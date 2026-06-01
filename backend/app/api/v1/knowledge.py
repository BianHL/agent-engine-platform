import os
import uuid
from pathlib import Path

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, get_tenant_id
from app.core.database import get_db
from app.core.rbac import require_permission
from app.engines.knowledge_engine.chunker.chunker import DocumentChunker
from app.engines.knowledge_engine.parser.pdf_parser import PDFParser
from app.engines.knowledge_engine.parser.word_parser import WordParser
from app.engines.knowledge_engine.parser.ppt_parser import PPTParser
from app.engines.knowledge_engine.parser.excel_parser import ExcelParser
from app.engines.knowledge_engine.parser.text_parser import TextParser
from app.engines.knowledge_engine.parser.web_parser import WebParser
from app.models.base import DocumentModel, KnowledgeBaseModel
from app.platform.knowledge_service.knowledge_service import KnowledgeBaseService
from app.schemas.api import (
    CreateKnowledgeBaseRequest,
    DocumentResponse,
    KnowledgeBaseResponse,
    PaginatedResponse,
    StatusResponse)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class AddUrlRequest(BaseModel):
    url: str
    chunk_size: int = Field(500, ge=100, le=2000)
    chunk_overlap: int = Field(50, ge=0, le=500)


class CrawlUrlRequest(BaseModel):
    url: str
    max_pages: int = Field(10, ge=1, le=100)
    allowed_domains: Optional[List[str]] = None
    chunk_size: int = Field(500, ge=100, le=2000)
    chunk_overlap: int = Field(50, ge=0, le=500)

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/uploads")

PARSERS = {
    ".pdf": PDFParser(),
    ".docx": WordParser(),
    ".doc": WordParser(),
    ".pptx": PPTParser(),
    ".xlsx": ExcelParser(),
    ".xls": ExcelParser(),
    ".txt": TextParser(),
    ".csv": TextParser(),
    ".html": TextParser(),
    ".htm": TextParser(),
    ".md": TextParser(),
    ".json": TextParser(),
    ".xml": TextParser(),
}


@router.post("/bases", status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    body: CreateKnowledgeBaseRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("knowledge", "create"))):
    """Create a new knowledge base."""
    svc = KnowledgeBaseService(db)
    return await svc.create(tenant_id=user["tenant_id"], data=body.model_dump(by_alias=True))


@router.get("/bases/{kb_id}")
async def get_knowledge_base(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    svc = KnowledgeBaseService(db)
    result = await svc.get(kb_id, tenant_id=user["tenant_id"])
    if not result:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return result


@router.get("/bases")
async def list_knowledge_bases(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user)):
    svc = KnowledgeBaseService(db)
    return await svc.list(tenant_id=user["tenant_id"], page=page, size=size)


@router.post("/bases/{kb_id}/documents")
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("knowledge", "upload"))):
    tenant_id = user["tenant_id"]

    # Verify knowledge base exists and belongs to tenant
    stmt = select(KnowledgeBaseModel).where(
        KnowledgeBaseModel.id == kb_id,
        KnowledgeBaseModel.tenant_id == tenant_id)
    result = await db.execute(stmt)
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # Validate file extension
    filename = file.filename or "upload.bin"
    ext = Path(filename).suffix.lower()
    if ext not in PARSERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(PARSERS.keys())}")

    # Save file to disk
    doc_id = str(uuid.uuid4())
    upload_path = Path(UPLOAD_DIR) / tenant_id / kb_id
    upload_path.mkdir(parents=True, exist_ok=True)
    file_path = upload_path / f"{doc_id}{ext}"

    # Read and validate file size (max 100MB)
    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 100MB.")
    file_path.write_bytes(content)

    # Create document record
    doc = DocumentModel(
        id=doc_id,
        tenant_id=tenant_id,
        knowledge_base_id=kb_id,
        filename=filename,
        file_type=ext,
        file_size=len(content),
        file_path=str(file_path),
        status="processing")
    db.add(doc)
    await db.flush()

    # Parse and chunk synchronously (async task queue is a future enhancement)
    try:
        parser = PARSERS[ext]
        parsed = parser.safe_parse(str(file_path))
        text_content = parsed.get("content", "")

        chunker = DocumentChunker(
            chunk_size=kb.chunk_size or 500,
            chunk_overlap=kb.chunk_overlap or 50)
        chunks = chunker.chunk_text(text_content, strategy=kb.chunking_strategy or "recursive")

        doc.chunk_count = len(chunks)
        doc.status = "ready"
        kb.document_count = (kb.document_count or 0) + 1
        await db.flush()
    except Exception as e:
        doc.status = "failed"
        doc.error_message = str(e)[:500]
        await db.flush()

    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "chunk_count": doc.chunk_count,
        "status": doc.status,
        "error_message": doc.error_message,
    }


@router.post("/bases/{kb_id}/documents/url")
async def add_url_to_knowledge_base(
    kb_id: str,
    body: AddUrlRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("knowledge", "upload"))):
    """Add a web page URL as a document to the knowledge base."""
    tenant_id = user["tenant_id"]

    stmt = select(KnowledgeBaseModel).where(
        KnowledgeBaseModel.id == kb_id,
        KnowledgeBaseModel.tenant_id == tenant_id)
    result = await db.execute(stmt)
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    web_parser = WebParser()
    try:
        parsed = await web_parser.parse(body.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {str(e)}")

    content = parsed.content
    if not content.strip():
        raise HTTPException(status_code=400, detail="No content extracted from URL")

    doc_id = str(uuid.uuid4())
    title = parsed.metadata.get("title", body.url)
    doc = DocumentModel(
        id=doc_id,
        tenant_id=tenant_id,
        knowledge_base_id=kb_id,
        filename=title,
        file_type="url",
        file_size=len(content.encode()),
        file_path=body.url,
        status="processing")
    db.add(doc)
    await db.flush()

    try:
        chunker = DocumentChunker(
            chunk_size=body.chunk_size,
            chunk_overlap=body.chunk_overlap)
        chunks = chunker.chunk_text(content, strategy=kb.chunking_strategy or "recursive")

        doc.chunk_count = len(chunks)
        doc.status = "ready"
        kb.document_count = (kb.document_count or 0) + 1
        await db.flush()
    except Exception as e:
        doc.status = "failed"
        doc.error_message = str(e)[:500]
        await db.flush()

    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": "url",
        "file_size": doc.file_size,
        "chunk_count": doc.chunk_count,
        "status": doc.status,
        "source_url": body.url,
    }


@router.post("/bases/{kb_id}/documents/crawl")
async def crawl_url_to_knowledge_base(
    kb_id: str,
    body: CrawlUrlRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("knowledge", "upload"))):
    """Crawl a website and add pages as documents to the knowledge base."""
    tenant_id = user["tenant_id"]

    stmt = select(KnowledgeBaseModel).where(
        KnowledgeBaseModel.id == kb_id,
        KnowledgeBaseModel.tenant_id == tenant_id)
    result = await db.execute(stmt)
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    web_parser = WebParser()
    try:
        pages = await web_parser.crawl(
            start_url=body.url,
            max_pages=body.max_pages,
            allowed_domains=body.allowed_domains)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Crawl failed: {str(e)}")

    if not pages:
        raise HTTPException(status_code=400, detail="No pages were successfully crawled")

    results = []
    for page in pages:
        content = web_parser._extract_content(page.content)
        if not content.strip():
            continue

        doc_id = str(uuid.uuid4())
        title = page.title or page.url
        doc = DocumentModel(
            id=doc_id,
            tenant_id=tenant_id,
            knowledge_base_id=kb_id,
            filename=title,
            file_type="url",
            file_size=len(content.encode()),
            file_path=page.url,
            status="processing")
        db.add(doc)
        await db.flush()

        try:
            chunker = DocumentChunker(
                chunk_size=body.chunk_size,
                chunk_overlap=body.chunk_overlap)
            chunks = chunker.chunk_text(content, strategy=kb.chunking_strategy or "recursive")

            doc.chunk_count = len(chunks)
            doc.status = "ready"
            kb.document_count = (kb.document_count or 0) + 1
            await db.flush()
        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)[:500]
            await db.flush()

        results.append({
            "id": doc.id,
            "filename": doc.filename,
            "file_type": "url",
            "chunk_count": doc.chunk_count,
            "status": doc.status,
            "source_url": page.url,
        })

    return {
        "total_pages": len(pages),
        "processed": len(results),
        "documents": results,
    }


@router.delete("/bases/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("knowledge", "delete"))):
    svc = KnowledgeBaseService(db)
    await svc.delete(kb_id, tenant_id=user["tenant_id"])
    return {"status": "deleted"}
