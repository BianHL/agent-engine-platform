"""Knowledge Base and Document models."""
from datetime import UTC, datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, EnterpriseMixin, OptimisticLockMixin, generate_uuid


class KnowledgeBaseModel(Base, EnterpriseMixin, OptimisticLockMixin):
    __tablename__ = "knowledge_bases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    icon_url = Column(String(500), nullable=True)
    embedding_model = Column(String(100))
    embedding_dimensions = Column(Integer)
    vector_collection = Column(String(200))
    es_index = Column(String(200))
    graph_enabled = Column(Boolean, default=False)
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=50)
    chunking_strategy = Column(String(20), default="recursive")
    retrieval_mode = Column(String(20), default="hybrid")
    retrieval_top_k = Column(Integer, default=5)
    score_threshold = Column(Float, default=0.5)
    rerank_enabled = Column(Boolean, default=False)
    rerank_model = Column(String(100), nullable=True)
    document_count = Column(Integer, default=0)
    segment_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    status = Column(String(20), default="active", index=True)
    last_synced_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1)

    # relationships
    tenant = relationship("TenantModel", back_populates="knowledge_bases")
    documents = relationship("DocumentModel", back_populates="knowledge_base", cascade="all, delete-orphan")


class DocumentModel(Base, EnterpriseMixin, OptimisticLockMixin):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), index=True, nullable=False)
    knowledge_base_id = Column(String(36), ForeignKey("knowledge_bases.id"), index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20))
    file_size = Column(BigInteger)
    file_path = Column(String(500))
    file_hash = Column(String(64), nullable=True, index=True)
    title = Column(String(500), nullable=True)
    author = Column(String(200), nullable=True)
    language = Column(String(10), nullable=True)
    page_count = Column(Integer, nullable=True)
    chunk_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    status = Column(String(20), default="pending", index=True)
    error_message = Column(Text)
    task_id = Column(String(100))
    processed_at = Column(DateTime, nullable=True)
    vector_indexed = Column(Boolean, default=False)
    es_indexed = Column(Boolean, default=False)
    graph_indexed = Column(Boolean, default=False)
    version = Column(Integer, default=1)

    # relationships
    knowledge_base = relationship("KnowledgeBaseModel", back_populates="documents")
    segments = relationship("DocumentSegmentModel", back_populates="document", cascade="all, delete-orphan")


class DocumentSegmentModel(Base):
    __tablename__ = "document_segments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), index=True, nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    knowledge_base_id = Column(String(36), index=True, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=True, index=True)
    segment_index = Column(Integer, nullable=False)
    token_count = Column(Integer)
    vector_id = Column(String(200))
    embedding_model = Column(String(100), nullable=True)
    parent_id = Column(String(36), ForeignKey("document_segments.id"), nullable=True, index=True)
    chunk_type = Column(String(20), default="text")
    chunk_metadata = Column(JSON, default=dict)
    hit_count = Column(Integer, default=0)
    last_hit_at = Column(DateTime, nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    document = relationship("DocumentModel", back_populates="segments")
    parent = relationship("DocumentSegmentModel", remote_side=[id], backref="children")
