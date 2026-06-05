"""Unit tests for file_ops and web_search builtin tools."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.engines.tool_engine.builtin.file_ops import (
    ALLOWED_BASE_DIRS,
    _validate_path,
    _execute as file_execute,
    file_ops_tool,
)
from app.engines.tool_engine.builtin.web_search import (
    _execute as search_execute,
    web_search_tool,
)


# ---------------------------------------------------------------------------
# file_ops: _validate_path
# ---------------------------------------------------------------------------


class TestFilePathValidation:
    def test_allowed_path_tmp(self):
        """Paths under /tmp/agent_files should be allowed."""
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            with patch("app.engines.tool_engine.builtin.file_ops.ALLOWED_BASE_DIRS", [tmpdir]):
                test_file = os.path.join(tmpdir, "test.txt")
                result = _validate_path(test_file)
                assert result is not None

    def test_blocked_path_outside_allowed(self):
        """Paths outside allowed directories should be rejected."""
        result = _validate_path("/etc/passwd")
        assert result is None

    def test_blocked_path_traversal(self):
        """Path traversal attempts should be rejected."""
        result = _validate_path("/app/uploads/../../etc/passwd")
        assert result is None

    def test_blocked_path_etc(self):
        result = _validate_path("/etc/hostname")
        assert result is None

    def test_blocked_path_root(self):
        result = _validate_path("/")
        assert result is None


# ---------------------------------------------------------------------------
# file_ops: _execute
# ---------------------------------------------------------------------------


class TestFileOpsExecute:
    @pytest.mark.asyncio
    async def test_blocked_path_returns_error(self):
        result = await file_execute({"operation": "read", "path": "/etc/passwd"})
        assert "error" in result
        assert "not in allowed" in result["error"]

    @pytest.mark.asyncio
    async def test_read_existing_file(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            Path(test_file).write_text("hello world")

            with patch("app.engines.tool_engine.builtin.file_ops.ALLOWED_BASE_DIRS", [tmpdir]):
                result = await file_execute({"operation": "read", "path": test_file})

        assert result["content"] == "hello world"

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            test_file = os.path.join(tmpdir, "missing.txt")

            with patch("app.engines.tool_engine.builtin.file_ops.ALLOWED_BASE_DIRS", [tmpdir]):
                result = await file_execute({"operation": "read", "path": test_file})

        assert "error" in result
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_write_file(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            test_file = os.path.join(tmpdir, "output.txt")

            with patch("app.engines.tool_engine.builtin.file_ops.ALLOWED_BASE_DIRS", [tmpdir]):
                result = await file_execute({
                    "operation": "write", "path": test_file, "content": "data",
                })
                assert result["success"] is True
                assert Path(test_file).read_text() == "data"

    @pytest.mark.asyncio
    async def test_list_directory(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            Path(os.path.join(tmpdir, "a.txt")).write_text("a")
            Path(os.path.join(tmpdir, "b.txt")).write_text("bb")

            with patch("app.engines.tool_engine.builtin.file_ops.ALLOWED_BASE_DIRS", [tmpdir]):
                result = await file_execute({"operation": "list", "path": tmpdir})

        assert len(result["entries"]) == 2
        names = {e["name"] for e in result["entries"]}
        assert "a.txt" in names

    @pytest.mark.asyncio
    async def test_list_nonexistent_directory(self):
        with patch("app.engines.tool_engine.builtin.file_ops.ALLOWED_BASE_DIRS", ["/nonexistent"]):
            result = await file_execute({"operation": "list", "path": "/nonexistent/dir"})

        assert "error" in result

    @pytest.mark.asyncio
    async def test_exists_true(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            test_file = os.path.join(tmpdir, "exists.txt")
            Path(test_file).write_text("x")

            with patch("app.engines.tool_engine.builtin.file_ops.ALLOWED_BASE_DIRS", [tmpdir]):
                result = await file_execute({"operation": "exists", "path": test_file})

        assert result["exists"] is True

    @pytest.mark.asyncio
    async def test_exists_false(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            test_file = os.path.join(tmpdir, "nope.txt")

            with patch("app.engines.tool_engine.builtin.file_ops.ALLOWED_BASE_DIRS", [tmpdir]):
                result = await file_execute({"operation": "exists", "path": test_file})

        assert result["exists"] is False

    @pytest.mark.asyncio
    async def test_unknown_operation(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
            with patch("app.engines.tool_engine.builtin.file_ops.ALLOWED_BASE_DIRS", [tmpdir]):
                result = await file_execute({"operation": "delete", "path": tmpdir})

        assert "error" in result

    @pytest.mark.asyncio
    async def test_tool_definition(self):
        assert file_ops_tool.name == "file_ops"
        assert "operation" in file_ops_tool.input_schema["required"]
        assert "path" in file_ops_tool.input_schema["required"]


# ---------------------------------------------------------------------------
# web_search: _execute
# ---------------------------------------------------------------------------


class TestWebSearch:
    @pytest.mark.asyncio
    async def test_successful_search(self):
        mock_results = [
            {"title": "Result 1", "href": "https://example.com/1", "body": "Snippet 1"},
            {"title": "Result 2", "href": "https://example.com/2", "body": "Snippet 2"},
        ]

        mock_ddgs_module = MagicMock()
        mock_instance = MagicMock()
        mock_instance.text.return_value = mock_results
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_ddgs_module.DDGS.return_value = mock_instance

        with patch.dict("sys.modules", {"duckduckgo_search": mock_ddgs_module}):
            result = await search_execute({"query": "test", "max_results": 2})

        assert len(result["results"]) == 2
        assert result["results"][0]["title"] == "Result 1"
        assert result["results"][0]["url"] == "https://example.com/1"

    @pytest.mark.asyncio
    async def test_missing_package(self):
        with patch.dict("sys.modules", {"duckduckgo_search": None}):
            result = await search_execute({"query": "test"})

        assert result["results"] == []
        assert "error" in result

    @pytest.mark.asyncio
    async def test_search_exception(self):
        mock_ddgs_module = MagicMock()
        mock_ddgs_module.DDGS.side_effect = RuntimeError("network error")

        with patch.dict("sys.modules", {"duckduckgo_search": mock_ddgs_module}):
            result = await search_execute({"query": "test"})

        assert result["results"] == []
        assert "error" in result

    @pytest.mark.asyncio
    async def test_tool_definition(self):
        assert web_search_tool.name == "web_search"
        assert "query" in web_search_tool.input_schema["required"]
