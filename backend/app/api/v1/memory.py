"""Memory engine API endpoints.

These routes expose the MemoryEngine's context retrieval, search, and
session-clearing capabilities.  The MemoryEngine itself depends on Redis
and optional vector-store backends; the routes retrieve the engine from
the application state (set during startup).
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.rbac import require_permission
from app.core.database import get_db
from app.schemas.api import MemoryContextResponse, MemorySearchRequest, StatusResponse

router = APIRouter(prefix="/memory", tags=["memory"])


def _get_memory_engine(request: Request):
    """Retrieve the MemoryEngine from app state."""
    engine = getattr(request.app.state, "memory_engine", None)
    if not engine:
        raise HTTPException(
            status_code=503,
            detail="Memory engine not available")
    return engine


@router.get("/context/{conversation_id}")
async def get_memory_context(
    conversation_id: str,
    request: Request,
    query: str = "",
    user: dict = Depends(get_current_user)):
    """Get memory context for a conversation (short-term, working, long-term)."""
    engine = _get_memory_engine(request)
    context = await engine.get_context(
        session_id=conversation_id,
        tenant_id=user["tenant_id"],
        user_id=user["id"],
        query=query)
    return context


@router.post("/search")
async def search_memory(
    body: MemorySearchRequest,
    request: Request,
    user: dict = Depends(require_permission("memory", "create"))):
    """Search long-term memory for relevant memories."""
    engine = _get_memory_engine(request)
    if not engine.long_term:
        raise HTTPException(
            status_code=503,
            detail="Long-term memory not available")
    results = await engine.long_term.search(
        query=body.query,
        tenant_id=user["tenant_id"],
        user_id=user["id"],
        top_k=body.limit)
    return results


@router.delete("/{conversation_id}", status_code=204)
async def clear_memory(
    conversation_id: str,
    request: Request,
    user: dict = Depends(require_permission("memory", "delete"))):
    """Clear short-term memory for a conversation session."""
    engine = _get_memory_engine(request)
    await engine.clear_session(conversation_id)
    return None
