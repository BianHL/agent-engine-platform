"""Built-in tool: file operations within restricted directories."""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from app.engines.tool_engine.registry import ToolDef

logger = logging.getLogger(__name__)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "operation": {
            "type": "string",
            "enum": ["read", "write", "list", "exists"],
            "description": "File operation to perform",
        },
        "path": {"type": "string", "description": "File path (relative to allowed directories)"},
        "content": {"type": "string", "description": "Content to write (for write operation)"},
        "encoding": {"type": "string", "default": "utf-8"},
    },
    "required": ["operation", "path"],
}

# Base directories where file operations are allowed
ALLOWED_BASE_DIRS = [
    "/app/uploads",
    "/app/data",
    "/tmp/agent_files",
]


def _validate_path(path: str) -> str | None:
    """Validate and resolve path, ensuring it's within allowed directories."""
    resolved = os.path.realpath(path)
    for base in ALLOWED_BASE_DIRS:
        if resolved.startswith(os.path.realpath(base)):
            return resolved
    return None


async def _execute(params: dict[str, Any]) -> dict[str, Any]:
    """Execute a file operation."""
    operation = params["operation"]
    path = params["path"]
    content = params.get("content", "")
    encoding = params.get("encoding", "utf-8")

    resolved = _validate_path(path)
    if not resolved:
        return {"error": f"Path not in allowed directories: {path}"}

    try:
        loop = asyncio.get_event_loop()

        if operation == "read":
            def _read():
                p = Path(resolved)
                if not p.exists():
                    return {"error": "File not found"}
                if p.stat().st_size > 1_000_000:  # 1MB limit
                    return {"error": "File too large (>1MB)"}
                return {"content": p.read_text(encoding=encoding)}

            return await loop.run_in_executor(None, _read)

        elif operation == "write":
            def _write():
                p = Path(resolved)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding=encoding)
                return {"success": True, "path": resolved}

            return await loop.run_in_executor(None, _write)

        elif operation == "list":
            def _list():
                p = Path(resolved)
                if not p.exists():
                    return {"error": "Directory not found"}
                if not p.is_dir():
                    return {"error": "Not a directory"}
                entries = []
                for entry in sorted(p.iterdir()):
                    entries.append({
                        "name": entry.name,
                        "type": "dir" if entry.is_dir() else "file",
                        "size": entry.stat().st_size if entry.is_file() else None,
                    })
                return {"entries": entries[:200]}  # Limit entries

            return await loop.run_in_executor(None, _list)

        elif operation == "exists":
            return {"exists": os.path.exists(resolved), "path": resolved}

        else:
            return {"error": f"Unknown operation: {operation}"}

    except Exception as e:
        logger.error("File operation failed: %s", e)
        return {"error": f"Operation failed: {e}"}


file_ops_tool = ToolDef(
    name="file_ops",
    description="Read, write, list, or check existence of files within allowed directories.",
    tool_type="builtin",
    input_schema=INPUT_SCHEMA,
    handler=_execute,
    permissions=["tool:file_ops"],
)
