"""Feedback and annotation API endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.base import MessageFeedbackModel, MessageAnnotationModel, MessageModel
from app.schemas.api import (
    CreateAnnotationRequest,
    CreateFeedbackRequest,
    UpdateFeedbackRequest,
)

router = APIRouter(prefix="/feedbacks", tags=["feedbacks"])


# ---------------------------------------------------------------------------
# Message Feedbacks (positive/negative rating + comment)
# ---------------------------------------------------------------------------

@router.post("")
async def create_feedback(
    body: CreateFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create feedback for a message (positive/negative rating + comment)."""
    message_id = body.message_id
    rating = body.rating

    # Verify message exists
    stmt = select(MessageModel).where(MessageModel.id == message_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Message not found")

    # Check for existing feedback from this user on this message
    stmt = select(MessageFeedbackModel).where(
        MessageFeedbackModel.message_id == message_id,
        MessageFeedbackModel.user_id == user.get("id"),
    )
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Feedback already exists for this message")

    feedback = MessageFeedbackModel(
        message_id=message_id,
        user_id=user.get("id"),
        rating=rating,
        comment=body.comment,
    )
    db.add(feedback)
    await db.flush()

    return {
        "id": feedback.id,
        "message_id": message_id,
        "rating": feedback.rating,
        "comment": feedback.comment,
    }


@router.put("/{feedback_id}")
async def update_feedback(
    feedback_id: str,
    body: UpdateFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Update an existing feedback."""
    stmt = select(MessageFeedbackModel).where(
        MessageFeedbackModel.id == feedback_id,
        MessageFeedbackModel.user_id == user.get("id"),
    )
    result = await db.execute(stmt)
    feedback = result.scalar_one_or_none()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    if body.rating is not None:
        feedback.rating = body.rating
    if body.comment is not None:
        feedback.comment = body.comment
    await db.flush()

    return {"status": "updated"}


@router.get("/stats/{agent_id}")
async def get_feedback_stats(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get feedback statistics for an agent."""
    stmt = select(
        func.count(MessageFeedbackModel.id).label("total"),
        func.count().filter(MessageFeedbackModel.rating == "positive").label("positive"),
        func.count().filter(MessageFeedbackModel.rating == "negative").label("negative"),
    ).join(
        MessageModel, MessageFeedbackModel.message_id == MessageModel.id
    )
    result = await db.execute(stmt)
    row = result.one()
    total = row.total or 0
    return {
        "total_feedbacks": total,
        "positive": row.positive or 0,
        "negative": row.negative or 0,
        "positive_rate": round(row.positive / total * 100, 1) if total > 0 else 0,
    }


# ---------------------------------------------------------------------------
# Message Annotations (corrected answers)
# ---------------------------------------------------------------------------

@router.post("/annotations")
async def create_annotation(
    body: CreateAnnotationRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create an annotation (corrected answer) for a message."""
    message_id = body.message_id
    corrected_answer = body.corrected_answer

    # Verify message exists
    stmt = select(MessageModel).where(MessageModel.id == message_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Message not found")

    annotation = MessageAnnotationModel(
        message_id=message_id,
        tenant_id=user["tenant_id"],
        corrected_answer=corrected_answer,
        question=body.question,
    )
    db.add(annotation)
    await db.flush()

    return {
        "id": annotation.id,
        "message_id": message_id,
        "corrected_answer": corrected_answer,
    }


@router.get("/annotations")
async def list_annotations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List annotations for the current tenant."""
    stmt = (
        select(MessageAnnotationModel)
        .where(MessageAnnotationModel.tenant_id == user["tenant_id"])
        .order_by(MessageAnnotationModel.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(stmt)
    return [
        {
            "id": a.id,
            "message_id": a.message_id,
            "question": a.question,
            "corrected_answer": a.corrected_answer,
            "hit_count": a.hit_count,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in result.scalars().all()
    ]
