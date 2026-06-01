"""Knowledge Base related schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CreateKnowledgeBaseRequest(BaseModel):
    name: str
    description: str = ""
    icon_url: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_dimensions: int = Field(1536, alias="dimensions")
    graph_enabled: bool = False
    chunk_size: int = 500
    chunk_overlap: int = 50
    chunking_strategy: str = "recursive"
    retrieval_mode: str = "hybrid"
    retrieval_top_k: int = 5
    score_threshold: float = 0.5
    rerank_enabled: bool = False
    rerank_model: Optional[str] = None

    class Config:
        populate_by_name = True


class UpdateKnowledgeBaseRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    embedding_model: Optional[str] = None
    graph_enabled: Optional[bool] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    chunking_strategy: Optional[str] = None
    retrieval_mode: Optional[str] = None
    retrieval_top_k: Optional[int] = None
    score_threshold: Optional[float] = None
    rerank_enabled: Optional[bool] = None
    rerank_model: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str
    icon_url: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_dimensions: Optional[int] = None
    vector_collection: Optional[str] = None
    es_index: Optional[str] = None
    graph_enabled: bool = False
    chunk_size: int = 500
    chunk_overlap: int = 50
    chunking_strategy: str = "recursive"
    retrieval_mode: str = "hybrid"
    retrieval_top_k: int = 5
    score_threshold: float = 0.5
    rerank_enabled: bool = False
    rerank_model: Optional[str] = None
    document_count: int = 0
    segment_count: int = 0
    total_tokens: int = 0
    status: str
    last_synced_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: str
    knowledge_base_id: str
    filename: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None
    page_count: Optional[int] = None
    chunk_count: int = 0
    token_count: int = 0
    status: str
    error_message: Optional[str] = None
    task_id: Optional[str] = None
    processed_at: Optional[datetime] = None
    vector_indexed: bool = False
    es_indexed: bool = False
    graph_indexed: bool = False
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentSegmentResponse(BaseModel):
    id: str
    document_id: str
    knowledge_base_id: str
    content: str
    content_hash: Optional[str] = None
    segment_index: int
    token_count: Optional[int] = None
    vector_id: Optional[str] = None
    embedding_model: Optional[str] = None
    parent_id: Optional[str] = None
    chunk_type: str = "text"
    chunk_metadata: dict = {}
    hit_count: int = 0
    last_hit_at: Optional[datetime] = None
    enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
