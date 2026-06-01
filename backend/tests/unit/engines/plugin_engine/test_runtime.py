"""Tests for plugin sandbox runtime."""
import asyncio
import pytest
from app.engines.plugin_engine.runtime import PluginSandbox, PluginRuntime, PluginExecutionResult


@pytest.fixture
def sandbox():
    return PluginSandbox(timeout=10, max_memory_mb=128, max_cpu_seconds=10)


@pytest.fixture
def runtime():
    return PluginRuntime()


@pytest.mark.unit
class TestPluginExecutionResult:
    def test_to_dict(self):
        result = PluginExecutionResult(
            success=True, output={"key": "value"}, duration_ms=42.5
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["output"] == {"key": "value"}
        assert d["duration_ms"] == 42.5
        assert d["error"] is None
        assert d["exit_code"] == 0

    def test_to_dict_truncates_logs(self):
        long_log = "x" * 5000
        result = PluginExecutionResult(success=True, logs=long_log)
        assert len(result.to_dict()["logs"]) == 2000


@pytest.mark.unit
class TestPluginSandbox:
    @pytest.mark.asyncio
    async def test_successful_execution(self, sandbox):
        code = '''
def main(name="world"):
    return {"greeting": f"Hello, {name}!"}
'''
        result = await sandbox.execute(code, entry_point="main", params={"name": "Alice"})
        assert result.success is True
        assert result.output == {"greeting": "Hello, Alice!"}
        assert result.duration_ms > 0

    @pytest.mark.asyncio
    async def test_timeout_handling(self, sandbox):
        sandbox._timeout = 1
        code = '''
import time
def main():
    time.sleep(10)
    return {}
'''
        result = await sandbox.execute(code)
        assert result.success is False
        assert "timed out" in result.error

    @pytest.mark.asyncio
    async def test_missing_entry_point(self, sandbox):
        code = '''
def not_main():
    return {}
'''
        result = await sandbox.execute(code, entry_point="main")
        assert result.success is False
        assert "Entry point" in result.error or "not found" in result.error

    @pytest.mark.asyncio
    async def test_code_error_handling(self, sandbox):
        code = '''
def main():
    raise ValueError("intentional error")
'''
        result = await sandbox.execute(code)
        assert result.success is False
        assert "intentional error" in result.error

    @pytest.mark.asyncio
    async def test_resource_limits_basic(self, sandbox):
        sandbox._max_memory_mb = 32
        code = '''
def main():
    return {"ok": True}
'''
        result = await sandbox.execute(code)
        assert result.success is True
        assert result.output == {"ok": True}


@pytest.mark.unit
class TestPluginRuntime:
    @pytest.mark.asyncio
    async def test_execution_log(self, runtime):
        code = '''
def main():
    return {"result": 42}
'''
        result = await runtime.execute_plugin(
            plugin_id="test-plugin", code=code, tenant_id="t1"
        )
        assert result.success is True

        logs = runtime.get_execution_log()
        assert len(logs) == 1
        assert logs[0]["plugin_id"] == "test-plugin"
        assert logs[0]["tenant_id"] == "t1"
        assert logs[0]["success"] is True

    @pytest.mark.asyncio
    async def test_execution_log_filter_by_plugin(self, runtime):
        code = '''
def main():
    return {}
'''
        await runtime.execute_plugin(plugin_id="p1", code=code)
        await runtime.execute_plugin(plugin_id="p2", code=code)

        assert len(runtime.get_execution_log("p1")) == 1
        assert len(runtime.get_execution_log("p2")) == 1
        assert len(runtime.get_execution_log()) == 2

    @pytest.mark.asyncio
    async def test_plugin_failure_logged(self, runtime):
        code = '''
def main():
    raise RuntimeError("boom")
'''
        result = await runtime.execute_plugin(plugin_id="fail-plugin", code=code)
        assert result.success is False

        logs = runtime.get_execution_log("fail-plugin")
        assert len(logs) == 1
        assert logs[0]["success"] is False
