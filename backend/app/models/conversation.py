"""Conversation and Message models."""
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid


class ConversationModel(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    agent_id = Column(String(36), ForeignKey("agents.id"), index=True, nullable=False)
    agent_name = Column(String(100), nullable=True)
    title = Column(String(200))
    summary = Column(Text, nullable=True)
    model_provider = Column(String(50), nullable=True)
    model_name = Column(String(100), nullable=True)
    status = Column(String(20), default="active", index=True)
    is_pinned = Column(Boolean, default=False)
    message_count = Column(Integer, default=0)
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 6), default=0.0)
    last_message_at = Column(DateTime, nullable=True, index=True)
    last_message_preview = Column(String(200), nullable=True)
    archived_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    tenant = relationship("TenantModel", back_populates="conversations")
    user = relationship("UserModel", back_populates="conversations")
    agent = relationship("AgentModel", back_populates="conversations")
    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan")
    variables = relationship("ConversationVariableModel", back_populates="conversation", cascade="all, delete-orphan")


class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), index=True, nullable=False)
    tenant_id = Column(String(36), index=True, nullable=False)
    role = Column(String(20), nullable=False, index=True)
    content = Column(Text, nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    model_provider = Column(String(50), nullable=True)
    model_name = Column(String(100), nullable=True)
    tool_calls = Column(JSON, nullable=True)
    tool_call_id = Column(String(100), nullable=True)
    name = Column(String(100), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    first_token_ms = Column(Integer, nullable=True)
    message_metadata = Column(JSON, default=dict)
    citation_sources = Column(JSON, nullable=True)
    feedback_score = Column(String(10), nullable=True)
    meta_info = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), index=True)

    # relationships
    conversation = relationship("ConversationModel", back_populates="messages")
    feedbacks = relationship("MessageFeedbackModel", back_populates="message", cascade="all, delete-orphan")
    annotations = relationship("MessageAnnotationModel", back_populates="message", cascade="all, delete-orphan")


class ConversationVariableModel(Base):
    __tablename__ = "conversation_variables"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), index=True, nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    conversation = relationship("ConversationModel", back_populates="variables")


class MessageFeedbackModel(Base):
    __tablename__ = "message_feedbacks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    message_id = Column(String(36), ForeignKey("messages.id"), index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    rating = Column(String(10), nullable=False)
    comment = Column(Text)
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    message = relationship("MessageModel", back_populates="feedbacks")


class MessageAnnotationModel(Base):
    __tablename__ = "message_annotations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    message_id = Column(String(36), ForeignKey("messages.id"), index=True, nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    question = Column(Text)
    corrected_answer = Column(Text)
    annotation_type = Column(String(20), default="correction")
    hit_count = Column(Integer, default=0)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None))

    # relationships
    message = relationship("MessageModel", back_populates="annotations")
