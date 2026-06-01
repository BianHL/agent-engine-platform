"""Tool registry: central catalog of all available tools (builtin + custom)."""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ToolDef:
    """Definition of a single tool."""

    __slots__ = (
        "name",
        "description",
        "tool_type",
        "input_schema",
        "output_schema",
        "handler",
        "config",
        "permissions",
    )

    def __init__(
        self,
        name: str,
        description: str,
        tool_type: str,
        input_schema: dict,
        handler: Callable[..., Any],
        output_schema: Optional[dict] = None,
        config: Optional[dict] = None,
        permissions: Optional[list[str]] = None,
    ):
        self.name = name
        self.description = description
        self.tool_type = tool_type  # builtin / custom / mcp
        self.input_schema = input_schema
        self.output_schema = output_schema or {"type": "object"}
        self.handler = handler
        self.config = config or {}
        self.permissions = permissions or []

    def to_openai_function(self) -> dict:
        """Convert to OpenAI function-calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "tool_type": self.tool_type,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "config": self.config,
            "permissions": self.permissions,
        }


class ToolRegistry:
    """Singleton registry for all tools."""

    _instance: Optional[ToolRegistry] = None
    _tools: Dict[str, ToolDef]

    def __new__(cls) -> ToolRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance

    def register(self, tool: ToolDef) -> None:
        """Register a tool definition."""
        if tool.name in self._tools:
            logger.warning("Overwriting tool '%s'", tool.name)
        self._tools[tool.name] = tool
        logger.info("Registered tool: %s (%s)", tool.name, tool.tool_type)

    def unregister(self, name: str) -> bool:
        """Remove a tool by name."""
        return self._tools.pop(name, None) is not None

    def get(self, name: str) -> Optional[ToolDef]:
        return self._tools.get(name)

    def list_tools(
        self,
        tool_type: Optional[str] = None,
        permission: Optional[str] = None,
    ) -> list[ToolDef]:
        """List tools, optionally filtered by type or required permission."""
        tools = list(self._tools.values())
        if tool_type:
            tools = [t for t in tools if t.tool_type == tool_type]
        if permission:
            tools = [t for t in tools if permission in t.permissions]
        return tools

    def get_openai_tools(
        self, tool_names: Optional[list[str]] = None
    ) -> list[dict]:
        """Get OpenAI function-calling schema for specified tools."""
        tools = self._tools.values()
        if tool_names:
            tools = [t for t in tools if t.name in tool_names]
        return [t.to_openai_function() for t in tools]

    def clear(self) -> None:
        self._tools.clear()


def register_builtin_tools() -> None:
    """Register all built-in tools into the global registry."""
    from app.engines.tool_engine.builtin.web_search import web_search_tool
    from app.engines.tool_engine.builtin.calculator import calculator_tool
    from app.engines.tool_engine.builtin.code_executor import code_executor_tool
    from app.engines.tool_engine.builtin.http_request import http_request_tool
    from app.engines.tool_engine.builtin.db_query import db_query_tool
    from app.engines.tool_engine.builtin.file_ops import file_ops_tool
    from app.engines.tool_engine.builtin.text_processor import (
        text_summarizer_tool,
        json_processor_tool,
        hash_generator_tool,
        base64_codec_tool,
        uuid_generator_tool,
        regex_engine_tool,
        date_time_tool,
    )

    registry = ToolRegistry()
    for tool in [
        web_search_tool,
        calculator_tool,
        code_executor_tool,
        http_request_tool,
        db_query_tool,
        file_ops_tool,
        text_summarizer_tool,
        json_processor_tool,
        hash_generator_tool,
        base64_codec_tool,
        uuid_generator_tool,
        regex_engine_tool,
        date_time_tool,
    ]:
        registry.register(tool)
