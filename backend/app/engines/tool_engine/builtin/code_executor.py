"""Built-in tool: code execution in sandboxed subprocess."""
from __future__ import annotations

import ast
import asyncio
import logging
import os
import tempfile
from typing import Any

from app.engines.tool_engine.registry import ToolDef

logger = logging.getLogger(__name__)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {"type": "string", "description": "Python code to execute"},
        "timeout": {
            "type": "integer",
            "default": 30,
            "description": "Execution timeout in seconds",
        },
    },
    "required": ["code"],
}

BLOCKED_MODULES = frozenset({
    "subprocess", "shutil", "ctypes", "importlib",
    "socket", "http", "ftplib", "smtplib", "telnetlib",
    "os", "sys", "signal", "multiprocessing",
})


def _check_imports(code: str) -> str | None:
    """AST-level import check. Returns error message or None."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Syntax error: {e}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_mod = alias.name.split(".")[0]
                if root_mod in BLOCKED_MODULES:
                    return f"Blocked module: {root_mod}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_mod = node.module.split(".")[0]
                if root_mod in BLOCKED_MODULES:
                    return f"Blocked module: {root_mod}"
    return None


async def _execute(params: dict[str, Any]) -> dict[str, Any]:
    """Execute Python code in an isolated subprocess."""
    code = params["code"]
    timeout = params.get("timeout", 30)

    error = _check_imports(code)
    if error:
        return {"error": error, "stdout": "", "stderr": ""}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        script_path = f.name

    try:
        env = {
            k: v for k, v in os.environ.items()
            if k not in ("PYTHONPATH",)
        }
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = await asyncio.create_subprocess_exec(
            "python3", script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "stdout": stdout.decode("utf-8", errors="replace")[:10000],
                "stderr": stderr.decode("utf-8", errors="replace")[:5000],
                "exit_code": proc.returncode,
            }
        except asyncio.TimeoutError:
            proc.kill()
            return {"error": f"Execution timed out after {timeout}s", "stdout": "", "stderr": ""}
    finally:
        os.unlink(script_path)


code_executor_tool = ToolDef(
    name="code_executor",
    description="Execute Python code in a sandboxed subprocess.",
    tool_type="builtin",
    input_schema=INPUT_SCHEMA,
    handler=_execute,
    permissions=["tool:code_executor"],
)
