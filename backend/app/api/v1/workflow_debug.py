"""Workflow debug control API endpoints."""
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.core.auth import get_current_user
from app.engines.workflow_engine.workflow import DebugMode, DebugSession
from app.engines.workflow_engine.debug_store import get_debug_store

router = APIRouter(prefix="/workflows", tags=["workflow-debug"])

# In-memory step_events (asyncio.Event) keyed by workflow_id.
# These are runtime synchronization primitives that cannot be serialized to Redis.
_step_events: dict[str, dict[str, asyncio.Event]] = {}


def _session_to_dict(session: DebugSession) -> dict:
    """Serialize DebugSession to a JSON-compatible dict."""
    return {
        "mode": session.mode.value,
        "breakpoints": list(session.breakpoints),
        "paused_at": session.paused_at,
        "history": session.history,
    }


def _dict_to_session(data: dict) -> DebugSession:
    """Deserialize a dict back into a DebugSession."""
    return DebugSession(
        mode=DebugMode(data.get("mode", "record")),
        breakpoints=set(data.get("breakpoints", [])),
        paused_at=data.get("paused_at"),
        history=data.get("history", []),
    )


class StartDebugRequest(BaseModel):
    mode: DebugMode = DebugMode.RECORD
    breakpoints: list[str] = []


class ContinueDebugRequest(BaseModel):
    node_id: str


@router.post("/{workflow_id}/debug/start", status_code=status.HTTP_200_OK)
async def start_debug_session(
    workflow_id: str,
    body: StartDebugRequest,
    user: dict = Depends(get_current_user),
):
    """Start a debug session for a workflow."""
    session = DebugSession(
        mode=body.mode,
        breakpoints=set(body.breakpoints),
    )
    store = get_debug_store()
    await store.set(workflow_id, _session_to_dict(session))
    return {
        "workflow_id": workflow_id,
        "mode": session.mode.value,
        "breakpoints": list(session.breakpoints),
        "status": "started",
    }


@router.post("/{workflow_id}/debug/continue", status_code=status.HTTP_200_OK)
async def continue_debug_session(
    workflow_id: str,
    body: ContinueDebugRequest,
    user: dict = Depends(get_current_user),
):
    """Continue execution from a breakpoint or step-through pause."""
    store = get_debug_store()
    data = await store.get(workflow_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active debug session for workflow {workflow_id}",
        )

    wf_events = _step_events.get(workflow_id, {})
    if body.node_id in wf_events:
        wf_events[body.node_id].set()

    return {
        "workflow_id": workflow_id,
        "node_id": body.node_id,
        "status": "continued",
    }


@router.get("/{workflow_id}/debug/state")
async def get_debug_state(
    workflow_id: str,
    user: dict = Depends(get_current_user),
):
    """Get the current debug state of a workflow."""
    store = get_debug_store()
    data = await store.get(workflow_id)
    if not data:
        return {"workflow_id": workflow_id, "enabled": False}

    return {
        "workflow_id": workflow_id,
        "enabled": True,
        "mode": data.get("mode", "record"),
        "breakpoints": data.get("breakpoints", []),
        "paused_at": data.get("paused_at"),
        "history": data.get("history", []),
    }


@router.post("/{workflow_id}/debug/stop", status_code=status.HTTP_200_OK)
async def stop_debug_session(
    workflow_id: str,
    user: dict = Depends(get_current_user),
):
    """Stop (clear) an active debug session."""
    store = get_debug_store()
    data = await store.get(workflow_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active debug session for workflow {workflow_id}",
        )

    # Signal any waiting step events so paused coroutines can exit
    wf_events = _step_events.pop(workflow_id, {})
    for event in wf_events.values():
        event.set()

    await store.delete(workflow_id)

    return {
        "workflow_id": workflow_id,
        "status": "stopped",
    }
