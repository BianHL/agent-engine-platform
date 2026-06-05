"""Unit tests for ToolExecutor: permission checks, timeouts, execution logging."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.engines.tool_engine.executor import ToolExecutor
from app.engines.tool_engine.registry import ToolDef, ToolRegistry


def _make_mock_db():
    """Create a mock AsyncSession with flush tracking."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


def _make_mock_execution():
    """Create a mock ToolExecutionModel instance."""
    exec_obj = MagicMock()
    exec_obj.id = "exec-001"
    exec_obj.status = "pending"
    exec_obj.output_data = None
    exec_obj.error_message = None
    exec_obj.duration_ms = None
    exec_obj.created_at = None
    return exec_obj


def _register_tool(name="test_tool", handler=None, permissions=None):
    """Register a tool in the singleton registry."""
    ToolRegistry._instance = None
    reg = ToolRegistry()
    tool = ToolDef(
        name=name,
        description="test",
        tool_type="builtin",
        input_schema={"type": "object"},
        handler=handler or AsyncMock(return_value={"ok": True}),
        permissions=permissions or [],
    )
    reg.register(tool)
    return reg


# ---------------------------------------------------------------------------
# execute()
# ---------------------------------------------------------------------------


class TestExecutorExecute:
    def setup_method(self):
        ToolRegistry._instance = None

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        handler = AsyncMock(return_value={"data": "hello"})
        _register_tool(handler=handler)
        db = _make_mock_db()

        with patch("app.engines.tool_engine.executor.ToolExecutionModel", return_value=_make_mock_execution()):
            executor = ToolExecutor(db)
            result = await executor.execute("test_tool", {"x": 1}, tenant_id="t1")

        assert result["tool"] == "test_tool"
        assert result["result"] == {"data": "hello"}
        assert "duration_ms" in result
        assert "execution_id" in result
        handler.assert_called_once_with({"x": 1})

    @pytest.mark.asyncio
    async def test_tool_not_found(self):
        db = _make_mock_db()
        executor = ToolExecutor(db)
        result = await executor.execute("nonexistent", {}, tenant_id="t1")

        assert "error" in result
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_timeout(self):
        async def slow_handler(params):
            await asyncio.sleep(100)
            return {"never": "reached"}

        _register_tool(handler=slow_handler)
        db = _make_mock_db()

        with patch("app.engines.tool_engine.executor.ToolExecutionModel", return_value=_make_mock_execution()):
            executor = ToolExecutor(db)
            result = await executor.execute("test_tool", {}, tenant_id="t1", timeout=1)

        assert "error" in result
        assert "timed out" in result["error"]

    @pytest.mark.asyncio
    async def test_handler_exception(self):
        async def bad_handler(params):
            raise ValueError("something broke")

        _register_tool(handler=bad_handler)
        db = _make_mock_db()

        with patch("app.engines.tool_engine.executor.ToolExecutionModel", return_value=_make_mock_execution()):
            executor = ToolExecutor(db)
            result = await executor.execute("test_tool", {}, tenant_id="t1")

        assert "error" in result
        assert "something broke" in result["error"]

    @pytest.mark.asyncio
    async def test_execution_record_status_success(self):
        _register_tool()
        db = _make_mock_db()
        mock_exec = _make_mock_execution()

        with patch("app.engines.tool_engine.executor.ToolExecutionModel", return_value=mock_exec):
            executor = ToolExecutor(db)
            await executor.execute("test_tool", {}, tenant_id="t1")

        assert mock_exec.status == "success"
        assert mock_exec.duration_ms is not None

    @pytest.mark.asyncio
    async def test_execution_record_status_failed(self):
        async def bad_handler(params):
            raise RuntimeError("crash")

        _register_tool(handler=bad_handler)
        db = _make_mock_db()
        mock_exec = _make_mock_execution()

        with patch("app.engines.tool_engine.executor.ToolExecutionModel", return_value=mock_exec):
            executor = ToolExecutor(db)
            await executor.execute("test_tool", {}, tenant_id="t1")

        assert mock_exec.status == "failed"
        assert "crash" in mock_exec.error_message


# ---------------------------------------------------------------------------
# execute_for_agent()
# ---------------------------------------------------------------------------


class TestExecutorForAgent:
    def setup_method(self):
        ToolRegistry._instance = None

    @pytest.mark.asyncio
    async def test_agent_tool_call_success(self):
        _register_tool()
        db = _make_mock_db()

        agent_tools = [{"name": "test_tool", "type": "function"}]
        tool_call = {"name": "test_tool", "arguments": {"x": 1}}

        with patch("app.engines.tool_engine.executor.ToolExecutionModel", return_value=_make_mock_execution()):
            executor = ToolExecutor(db)
            result = await executor.execute_for_agent(agent_tools, tool_call, tenant_id="t1")

        assert result["tool"] == "test_tool"
        assert result["result"] == {"ok": True}

    @pytest.mark.asyncio
    async def test_agent_tool_not_allowed(self):
        _register_tool()
        db = _make_mock_db()

        agent_tools = [{"name": "other_tool"}]
        tool_call = {"name": "test_tool", "arguments": {}}

        executor = ToolExecutor(db)
        result = await executor.execute_for_agent(agent_tools, tool_call, tenant_id="t1")

        assert "error" in result
        assert "does not have access" in result["error"]

    @pytest.mark.asyncio
    async def test_agent_json_string_arguments(self):
        _register_tool()
        db = _make_mock_db()

        agent_tools = [{"name": "test_tool"}]
        tool_call = {"name": "test_tool", "arguments": '{"x": 42}'}

        with patch("app.engines.tool_engine.executor.ToolExecutionModel", return_value=_make_mock_execution()):
            executor = ToolExecutor(db)
            result = await executor.execute_for_agent(agent_tools, tool_call, tenant_id="t1")

        assert result["tool"] == "test_tool"

    @pytest.mark.asyncio
    async def test_agent_invalid_json_arguments(self):
        _register_tool()
        db = _make_mock_db()

        agent_tools = [{"name": "test_tool"}]
        tool_call = {"name": "test_tool", "arguments": "not-json{"}

        executor = ToolExecutor(db)
        result = await executor.execute_for_agent(agent_tools, tool_call, tenant_id="t1")

        assert "error" in result
        assert "Invalid tool arguments" in result["error"]


# ---------------------------------------------------------------------------
# get_execution_history()
# ---------------------------------------------------------------------------


class TestExecutionHistory:
    def setup_method(self):
        ToolRegistry._instance = None

    @pytest.mark.asyncio
    async def test_basic_history(self):
        mock_exec = MagicMock()
        mock_exec.id = "exec-1"
        mock_exec.tool_id = "test_tool"
        mock_exec.status = "success"
        mock_exec.duration_ms = 100
        mock_exec.input_data = {"x": 1}
        mock_exec.output_data = {"ok": True}
        mock_exec.error_message = None
        mock_exec.created_at = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_exec]

        db = _make_mock_db()
        db.execute = AsyncMock(return_value=mock_result)

        executor = ToolExecutor(db)
        history = await executor.get_execution_history(tenant_id="t1")

        assert len(history) == 1
        assert history[0]["tool"] == "test_tool"
        assert history[0]["status"] == "success"

    @pytest.mark.asyncio
    async def test_history_filtered_by_tool(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        db = _make_mock_db()
        db.execute = AsyncMock(return_value=mock_result)

        executor = ToolExecutor(db)
        history = await executor.get_execution_history(tenant_id="t1", tool_name="specific_tool")

        assert history == []
        db.execute.assert_called_once()
