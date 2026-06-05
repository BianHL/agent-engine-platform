"""Tools API: registration, execution, and custom tool management."""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.rbac import require_permission
from app.engines.tool_engine.executor import ToolExecutor
from app.engines.tool_engine.registry import ToolRegistry
from app.engines.tool_engine.schema_parser import parse_openapi_to_tools
from app.models.base import ToolModel
from app.schemas.api import CreateToolRequest, ExecuteToolRequest

router = APIRouter(prefix="/tools", tags=["tools"])


# ---------------------------------------------------------------------------
# Built-in tool listing (from registry)
# ---------------------------------------------------------------------------

@router.get("/builtin")
async def list_builtin_tools(
    user: dict = Depends(get_current_user)):
    """List all registered built-in tools."""
    registry = ToolRegistry()
    tools = registry.list_tools(tool_type="builtin")
    return [t.to_dict() for t in tools]


# ---------------------------------------------------------------------------
# Custom tool CRUD (database-backed)
# ---------------------------------------------------------------------------

@router.post("/")
async def create_custom_tool(
    body: CreateToolRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("tool", "create")),
):
    """Register a custom tool from an OpenAPI schema or manual definition."""
    tool_type = body.tool_type

    if tool_type == "custom" and body.api_schema:
        # Parse OpenAPI schema to extract tool definitions
        spec = body.api_schema
        tools = parse_openapi_to_tools(spec)
        if not tools:
            raise HTTPException(status_code=400, detail="No operations found in OpenAPI schema")

        created = []
        for tool_def in tools:
            tool = ToolModel(
                tenant_id=user["tenant_id"],
                name=tool_def.name,
                description=tool_def.description,
                tool_type="custom",
                api_schema=tool_def.to_dict(),
                config=tool_def.config,
                enabled=True,
            )
            db.add(tool)
            created.append(tool_def.name)

        await db.flush()
        return {"created": created, "count": len(created)}

    # Manual tool definition
    if not body.name:
        raise HTTPException(status_code=400, detail="name is required")

    tool = ToolModel(
        tenant_id=user["tenant_id"],
        name=body.name,
        description=body.description,
        tool_type=tool_type,
        api_schema=body.api_schema or {},
        config=body.config,
        enabled=body.enabled,
    )
    db.add(tool)
    await db.flush()

    return {"id": tool.id, "name": tool.name, "tool_type": tool.tool_type}


@router.get("/")
async def list_tools(
    tool_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List all tools (builtin + custom) for the current tenant."""
    # Get builtin tools from registry
    registry = ToolRegistry()
    builtin = registry.list_tools(tool_type="builtin")
    result = [{"name": t.name, "description": t.description, "tool_type": "builtin", "source": "registry"} for t in builtin]

    # Get custom tools from database
    stmt = select(ToolModel).where(ToolModel.tenant_id == user["tenant_id"])
    if tool_type:
        stmt = stmt.where(ToolModel.tool_type == tool_type)
    db_result = await db.execute(stmt)
    for tool in db_result.scalars().all():
        result.append({
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "tool_type": tool.tool_type,
            "enabled": tool.enabled,
            "source": "database",
        })

    return result


@router.get("/{tool_id}")
async def get_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get a tool by ID."""
    stmt = select(ToolModel).where(
        ToolModel.id == tool_id,
        ToolModel.tenant_id == user["tenant_id"],
    )
    result = await db.execute(stmt)
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description,
        "tool_type": tool.tool_type,
        "api_schema": tool.api_schema,
        "config": tool.config,
        "enabled": tool.enabled,
    }


@router.delete("/{tool_id}")
async def delete_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("tool", "delete")),
):
    """Delete a custom tool."""
    stmt = select(ToolModel).where(
        ToolModel.id == tool_id,
        ToolModel.tenant_id == user["tenant_id"],
    )
    result = await db.execute(stmt)
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    await db.delete(tool)
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

@router.post("/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    body: ExecuteToolRequest,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_permission("tool", "execute")),
):
    """Execute a tool by name."""
    params = body.params if body.params else body.model_dump(exclude={"timeout"})
    timeout = body.timeout

    executor = ToolExecutor(db)
    result = await executor.execute(
        tool_name=tool_name,
        params=params,
        tenant_id=user["tenant_id"],
        user_id=user.get("id"),
        timeout=timeout,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/executions/history")
async def get_execution_history(
    tool_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get tool execution history for the current tenant."""
    executor = ToolExecutor(db)
    return await executor.get_execution_history(
        tenant_id=user["tenant_id"],
        tool_name=tool_name,
        limit=limit,
    )
