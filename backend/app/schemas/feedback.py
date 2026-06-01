"""Feedback and Annotation related schemas."""
from typing import Optional

from pydantic import BaseModel, Field


class CreateFeedbackRequest(BaseModel):
    message_id: str
    rating: str = Field(..., pattern="^(positive|negative)$")
    comment: Optional[str] = None


class UpdateFeedbackRequest(BaseModel):
    rating: Optional[str] = Field(None, pattern="^(positive|negative)$")
    comment: Optional[str] = None


class CreateAnnotationRequest(BaseModel):
    message_id: str
    corrected_answer: str
    question: Optional[str] = None
