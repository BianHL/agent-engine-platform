"""Tool executor: runs tools with permission checks, timeouts, and logging."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.tool_engine.registry import ToolDef, ToolRegistry
from app.models.base import ToolExecutionModel

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30  # seconds


class ToolExecutor:
    """Executes tools with permission checks, timeouts, and execution logging."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.registry = ToolRegistry()

    async def execute(
        self,
        tool_name: str,
        params: dict[str, Any],
        tenant_id: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """Execute a tool by name with full lifecycle management."""
        # 1. Look up tool
        tool = self.registry.get(tool_name)
        if not tool:
            return {"error": f"Tool not found: {tool_name}"}

        # 2. Permission check (caller should have already verified, but double-check)
        if tool.permissions:
            logger.debug("Tool %s requires permissions: %s", tool_name, tool.permissions)

        # 3. Create execution record
        execution = ToolExecutionModel(
            tool_id=tool_name,  # For builtin tools, tool_id is the name
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
            input_data=params,
            status="running",
        )
        self.db.add(execution)
        await self.db.flush()

        # 4. Execute with timeout
        start_time = time.monotonic()
        try:
            result = await asyncio.wait_for(
                tool.handler(params),
                timeout=timeout,
            )
            duration_ms = int((time.monotonic() - start_time) * 1000)

            # Update execution record
            execution.output_data = result
            execution.status = "success"
            execution.duration_ms = duration_ms
            await self.db.flush()

            return {
                "tool": tool_name,
                "result": result,
                "duration_ms": duration_ms,
                "execution_id": execution.id,
            }

        except asyncio.TimeoutError:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            execution.status = "failed"
            execution.error_message = f"Timed out after {timeout}s"
            execution.duration_ms = duration_ms
            await self.db.flush()
            return {"error": f"Tool execution timed out after {timeout}s", "tool": tool_name}

        except Exception as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            execution.status = "failed"
            execution.error_message = str(e)[:2000]
            execution.duration_ms = duration_ms
            await self.db.flush()
            logger.error("Tool %s failed: %s", tool_name, e)
            return {"error": str(e), "tool": tool_name}

    async def execute_for_agent(
        self,
        agent_tools: list[dict],
        tool_call: dict[str, Any],
        tenant_id: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Execute a tool call from an agent (function-calling format).

        Args:
            agent_tools: List of tool definitions the agent has access to.
            tool_call: {"name": "tool_name", "arguments": {...}}
        """
        tool_name = tool_call.get("name", "")
        arguments = tool_call.get("arguments", {})

        # Verify agent has access to this tool
        allowed_names = {t.get("name") for t in agent_tools}
        if tool_name not in allowed_names:
            return {"error": f"Agent does not have access to tool: {tool_name}"}

        # Parse arguments if they're a JSON string
        if isinstance(arguments, str):
            import json
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                return {"error": "Invalid tool arguments: not valid JSON"}

        return await self.execute(
            tool_name=tool_name,
            params=arguments,
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )

    async def get_execution_history(
        self,
        tenant_id: str,
        tool_name: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Get recent tool execution history for a tenant."""
        from sqlalchemy import select

        stmt = (
            select(ToolExecutionModel)
            .where(ToolExecutionModel.tenant_id == tenant_id)
            .order_by(ToolExecutionModel.created_at.desc())
            .limit(limit)
        )
        if tool_name:
            stmt = stmt.where(ToolExecutionModel.tool_id == tool_name)

        result = await self.db.execute(stmt)
        return [
            {
                "id": ex.id,
                "tool": ex.tool_id,
                "status": ex.status,
                "duration_ms": ex.duration_ms,
                "input": ex.input_data,
                "output": ex.output_data,
                "error": ex.error_message,
                "created_at": ex.created_at.isoformat() if ex.created_at else None,
            }
            for ex in result.scalars().all()
        ]
