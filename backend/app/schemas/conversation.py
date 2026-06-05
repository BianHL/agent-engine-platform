"""Conversation and Chat related schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, model_validator


class CreateConversationRequest(BaseModel):
    agent_id: str
    title: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    user_id: str
    agent_id: str
    agent_name: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    status: str
    is_pinned: bool = False
    message_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: Decimal = Decimal("0")
    last_message_at: Optional[datetime] = None
    last_message_preview: Optional[str] = None
    archived_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    tool_calls: Optional[list] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    latency_ms: Optional[int] = None
    first_token_ms: Optional[int] = None
    message_metadata: dict = {}
    metadata: dict = {}
    citation_sources: Optional[list] = None
    feedback_score: Optional[str] = None
    created_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def _map_meta_info(cls, data: Any) -> Any:
        if hasattr(data, "meta_info") and not isinstance(data, dict):
            values = {}
            for field in cls.model_fields:
                if field == "metadata":
                    values["metadata"] = getattr(data, "meta_info", {})
                else:
                    values[field] = getattr(data, field, None)
            return values
        return data


class AddMessageRequest(BaseModel):
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ChatCompletionResponse(BaseModel):
    content: str
    model: str
    usage: dict
    conversation_id: Optional[str] = None


class MessageFeedbackRequest(BaseModel):
    rating: str  # positive / negative
    comment: Optional[str] = None
    tags: Optional[List[str]] = None


class MessageFeedbackResponse(BaseModel):
    id: str
    message_id: str
    user_id: str
    rating: str
    comment: Optional[str] = None
    tags: Optional[list] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
