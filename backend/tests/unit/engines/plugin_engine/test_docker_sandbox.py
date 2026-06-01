"""Tests for Docker plugin sandbox."""
import json
import sys
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from app.engines.plugin_engine.runtime import (
    DockerPluginSandbox,
    PluginExecutionResult,
    PluginSandbox,
    create_sandbox,
)


@pytest.fixture
def mock_docker_module():
    """Create a mock docker module."""
    mock_docker = MagicMock()
    mock_client = MagicMock()
    mock_docker.from_env.return_value = mock_client
    sys.modules["docker"] = mock_docker
    yield mock_docker, mock_client
    del sys.modules["docker"]


@pytest.fixture
def mock_docker_client(mock_docker_module):
    """Create a mock Docker client."""
    _, mock_client = mock_docker_module
    return mock_client


@pytest.fixture
def docker_sandbox(mock_docker_module):
    """Create a DockerPluginSandbox with mocked client."""
    return DockerPluginSandbox(timeout=10, memory_limit="128m")


@pytest.mark.unit
class TestDockerPluginSandbox:
    def test_init_defaults(self):
        sandbox = DockerPluginSandbox()
        assert sandbox._image == "python:3.11-slim"
        assert sandbox._timeout == 30
        assert sandbox._memory_limit == "256m"
        assert sandbox._cpu_period == 100000
        assert sandbox._cpu_quota == 50000
        assert sandbox._network_enabled is False

    def test_init_custom_values(self):
        sandbox = DockerPluginSandbox(
            image="python:3.12-slim",
            timeout=60,
            memory_limit="512m",
            cpu_period=200000,
            cpu_quota=100000,
            network_enabled=True,
        )
        assert sandbox._image == "python:3.12-slim"
        assert sandbox._timeout == 60
        assert sandbox._memory_limit == "512m"
        assert sandbox._cpu_period == 200000
        assert sandbox._cpu_quota == 100000
        assert sandbox._network_enabled is True

    @pytest.mark.asyncio
    async def test_docker_unavailable_fallback(self):
        mock_docker = MagicMock()
        mock_docker.from_env.side_effect = ImportError("No module named 'docker'")
        sys.modules["docker"] = mock_docker
        try:
            sandbox = DockerPluginSandbox()
            result = await sandbox.execute("def main(): return {}")
            assert result.success is False
            assert "Docker not available" in result.error
        finally:
            del sys.modules["docker"]

    @pytest.mark.asyncio
    async def test_docker_connection_error(self):
        mock_docker = MagicMock()
        mock_docker.from_env.side_effect = Exception("Cannot connect to Docker")
        sys.modules["docker"] = mock_docker
        try:
            sandbox = DockerPluginSandbox()
            result = await sandbox.execute("def main(): return {}")
            assert result.success is False
            assert "Cannot connect to Docker" in result.error
        finally:
            del sys.modules["docker"]

    @pytest.mark.asyncio
    async def test_successful_execution(self, docker_sandbox, mock_docker_client):
        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b'{"result": 42}'
        mock_docker_client.containers.run.return_value = mock_container

        code = 'def main(): return {"result": 42}'
        result = await docker_sandbox.execute(code, entry_point="main")

        assert result.success is True
        assert result.output == {"result": 42}
        assert result.duration_ms > 0
        mock_container.remove.assert_called_once_with(force=True)

    @pytest.mark.asyncio
    async def test_execution_with_params(self, docker_sandbox, mock_docker_client):
        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b'{"greeting": "Hello, Alice!"}'
        mock_docker_client.containers.run.return_value = mock_container

        code = 'def main(name="world"): return {"greeting": f"Hello, {name}!"}'
        result = await docker_sandbox.execute(
            code, entry_point="main", params={"name": "Alice"}
        )

        assert result.success is True
        assert result.output == {"greeting": "Hello, Alice!"}

    @pytest.mark.asyncio
    async def test_container_failure(self, docker_sandbox, mock_docker_client):
        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 1}
        mock_container.logs.return_value = b"Error: something went wrong"
        mock_docker_client.containers.run.return_value = mock_container

        result = await docker_sandbox.execute("def main(): return {}")

        assert result.success is False
        assert result.exit_code == 1
        assert "Error: something went wrong" in result.error

    @pytest.mark.asyncio
    async def test_timeout_handling(self, docker_sandbox, mock_docker_client):
        mock_container = MagicMock()
        mock_container.wait.side_effect = Exception("Timed out waiting for container")
        mock_docker_client.containers.run.return_value = mock_container

        code = '''
import time
def main():
    time.sleep(100)
    return {}
'''
        result = await docker_sandbox.execute(code)

        assert result.success is False
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_missing_entry_point(self, docker_sandbox, mock_docker_client):
        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 1}
        mock_container.logs.return_value = b'{"error": "Entry point \'main\' not found"}'
        mock_docker_client.containers.run.return_value = mock_container

        code = 'def not_main(): return {}'
        result = await docker_sandbox.execute(code, entry_point="main")

        assert result.success is False

    @pytest.mark.asyncio
    async def test_container_cleanup_on_success(self, docker_sandbox, mock_docker_client):
        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b'{"ok": true}'
        mock_docker_client.containers.run.return_value = mock_container

        await docker_sandbox.execute("def main(): return {}")

        mock_container.remove.assert_called_once_with(force=True)

    @pytest.mark.asyncio
    async def test_container_cleanup_on_failure(self, docker_sandbox, mock_docker_client):
        mock_container = MagicMock()
        mock_container.wait.side_effect = Exception("Container crashed")
        mock_docker_client.containers.run.return_value = mock_container

        await docker_sandbox.execute("def main(): return {}")

        mock_container.remove.assert_called_once_with(force=True)

    @pytest.mark.asyncio
    async def test_container_config(self, docker_sandbox, mock_docker_client):
        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b'{}'
        mock_docker_client.containers.run.return_value = mock_container

        await docker_sandbox.execute("def main(): return {}")

        call_kwargs = mock_docker_client.containers.run.call_args[1]
        assert call_kwargs["image"] == "python:3.11-slim"
        assert call_kwargs["detach"] is True
        assert call_kwargs["mem_limit"] == "128m"
        assert call_kwargs["cpu_period"] == 100000
        assert call_kwargs["cpu_quota"] == 50000
        assert call_kwargs["network_disabled"] is True
        assert call_kwargs["read_only"] is True
        assert "/tmp" in call_kwargs["tmpfs"]
        assert call_kwargs["labels"] == {"agent-engine-plugin": "true"}

    def test_build_wrapper(self, docker_sandbox):
        wrapper = docker_sandbox._build_wrapper(
            code="def main(): return {}",
            entry_point="main",
            params={"key": "value"},
            config={"setting": True},
        )
        assert "import json" in wrapper
        assert "def main(): return {}" in wrapper
        assert '"key"' in wrapper
        assert '"value"' in wrapper


@pytest.mark.unit
class TestCreateSandbox:
    def test_create_subprocess_sandbox(self):
        sandbox = create_sandbox(backend="subprocess")
        assert isinstance(sandbox, PluginSandbox)

    def test_create_docker_sandbox(self):
        sandbox = create_sandbox(backend="docker")
        assert isinstance(sandbox, DockerPluginSandbox)

    def test_create_default_sandbox(self):
        sandbox = create_sandbox()
        assert isinstance(sandbox, PluginSandbox)

    def test_create_sandbox_with_kwargs(self):
        sandbox = create_sandbox(backend="subprocess", timeout=60, max_memory_mb=512)
        assert isinstance(sandbox, PluginSandbox)
        assert sandbox._timeout == 60
        assert sandbox._max_memory_mb == 512

    def test_create_docker_sandbox_with_kwargs(self):
        sandbox = create_sandbox(
            backend="docker",
            image="python:3.12-slim",
            memory_limit="512m",
        )
        assert isinstance(sandbox, DockerPluginSandbox)
        assert sandbox._image == "python:3.12-slim"
        assert sandbox._memory_limit == "512m"
