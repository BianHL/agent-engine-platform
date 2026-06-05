"""Plugin sandbox runtime for safe execution."""
import asyncio
import json
import logging
import os
import resource
import signal
import tempfile
from typing import Any, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PluginExecutionResult:
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    exit_code: int = 0
    logs: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "exit_code": self.exit_code,
            "logs": self.logs[:2000],
        }


class PluginSandbox:
    """Execute plugin code in isolated subprocess with resource limits."""

    def __init__(
        self,
        timeout: int = 30,
        max_memory_mb: int = 256,
        max_cpu_seconds: int = 30,
        allowed_modules: Optional[set[str]] = None,
    ):
        self._timeout = timeout
        self._max_memory_mb = max_memory_mb
        self._max_cpu_seconds = max_cpu_seconds
        self._allowed_modules = allowed_modules or {
            "json", "math", "re", "datetime", "collections", "itertools",
            "functools", "typing", "hashlib", "base64", "urllib", "http",
        }

    async def execute(
        self,
        code: str,
        entry_point: str = "main",
        params: dict = None,
        config: dict = None,
    ) -> PluginExecutionResult:
        """Execute plugin code in sandbox."""
        import time
        start = time.time()

        params = params or {}
        config = config or {}

        # Build wrapper script
        wrapper = self._build_wrapper(code, entry_point, params, config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(wrapper)
            script_path = f.name

        def _preexec():
            os.setpgrp()
            limits = [
                (resource.RLIMIT_AS, self._max_memory_mb * 1024 * 1024),
                (resource.RLIMIT_CPU, self._max_cpu_seconds),
                (resource.RLIMIT_NOFILE, 64),
                (resource.RLIMIT_FSIZE, 10 * 1024 * 1024),
            ]
            for res, val in limits:
                try:
                    resource.setrlimit(res, (val, val))
                except (ValueError, OSError) as e:
                    logger.debug("Failed to set resource limit %s: %s", res, e)

        safe_env = {k: os.environ.get(k, "") for k in ("PATH", "HOME", "TMPDIR") if k in os.environ or k == "PATH"}

        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(
                "python3", script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=_preexec,
                env=safe_env,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self._timeout)
                duration_ms = (time.time() - start) * 1000

                if proc.returncode != 0:
                    return PluginExecutionResult(
                        success=False,
                        error=stderr.decode("utf-8", errors="replace")[:2000],
                        duration_ms=duration_ms,
                        exit_code=proc.returncode,
                        logs=stdout.decode("utf-8", errors="replace"),
                    )

                raw = stdout.decode("utf-8", errors="replace").strip()
                try:
                    output = json.loads(raw)
                except json.JSONDecodeError:
                    output = raw

                return PluginExecutionResult(
                    success=True,
                    output=output,
                    duration_ms=duration_ms,
                    exit_code=0,
                    logs="",
                )
            except asyncio.TimeoutError:
                if proc.returncode is None:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        proc.kill()
                return PluginExecutionResult(
                    success=False,
                    error=f"Plugin execution timed out after {self._timeout}s",
                    duration_ms=(time.time() - start) * 1000,
                )
        finally:
            if proc and proc.returncode is None:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    proc.kill()
            try:
                os.unlink(script_path)
            except OSError as e:
                logger.debug("Failed to clean up temp script %s: %s", script_path, e)

    def _build_wrapper(self, code: str, entry_point: str, params: dict, config: dict) -> str:
        params_repr = repr(params)
        config_repr = repr(config)
        entry_escaped = entry_point.replace("\\", "\\\\").replace('"', '\\"')
        return f'''
import json, sys
_params = {params_repr}
_config = {config_repr}
try:
    exec(compile({code!r}, "<plugin>", "exec"))
    func = locals().get("{entry_escaped}")
    if func is None:
        sys.stderr.write(json.dumps({{"error": "Entry point '{entry_escaped}' not found"}}))
        sys.exit(1)
    result = func(**_params)
    print(json.dumps(result, ensure_ascii=False, default=str))
except Exception as e:
    sys.stderr.write(json.dumps({{"error": str(e)}}))
    sys.exit(1)
'''


class PluginRuntime:
    """High-level plugin execution manager."""

    def __init__(self, sandbox_backend: str = "subprocess", **sandbox_kwargs):
        self._sandbox = create_sandbox(backend=sandbox_backend, **sandbox_kwargs)
        self._execution_log: list[dict] = []

    async def execute_plugin(
        self,
        plugin_id: str,
        code: str,
        entry_point: str = "main",
        params: dict = None,
        config: dict = None,
        tenant_id: str = None,
    ) -> PluginExecutionResult:
        """Execute a plugin with full lifecycle management."""
        logger.info(f"Executing plugin {plugin_id}, entry={entry_point}")

        result = await self._sandbox.execute(
            code=code,
            entry_point=entry_point,
            params=params,
            config=config,
        )

        log_entry = {
            "plugin_id": plugin_id,
            "tenant_id": tenant_id,
            "success": result.success,
            "duration_ms": result.duration_ms,
            "exit_code": result.exit_code,
        }
        self._execution_log.append(log_entry)

        if not result.success:
            logger.warning(f"Plugin {plugin_id} failed: {result.error}")
        else:
            logger.info(f"Plugin {plugin_id} completed in {result.duration_ms:.1f}ms")

        return result

    def get_execution_log(self, plugin_id: str = None) -> list[dict]:
        if plugin_id:
            return [e for e in self._execution_log if e["plugin_id"] == plugin_id]
        return self._execution_log


class DockerPluginSandbox:
    """Execute plugins in Docker containers for stronger isolation."""

    def __init__(
        self,
        image: str = "python:3.11-slim",
        timeout: int = 30,
        memory_limit: str = "256m",
        cpu_period: int = 100000,
        cpu_quota: int = 50000,
        network_enabled: bool = False,
    ):
        self._image = image
        self._timeout = timeout
        self._memory_limit = memory_limit
        self._cpu_period = cpu_period
        self._cpu_quota = cpu_quota
        self._network_enabled = network_enabled
        self._client = None

    def _get_client(self):
        if self._client is None:
            import docker
            self._client = docker.from_env()
        return self._client

    async def execute(
        self,
        code: str,
        entry_point: str = "main",
        params: dict = None,
        config: dict = None,
    ) -> PluginExecutionResult:
        """Execute plugin code in a Docker container."""
        import time
        start = time.time()

        params = params or {}
        config = config or {}

        wrapper = self._build_wrapper(code, entry_point, params, config)

        try:
            client = self._get_client()
        except Exception as e:
            return PluginExecutionResult(
                success=False,
                error=f"Docker not available: {e}",
                duration_ms=(time.time() - start) * 1000,
            )

        container = None
        try:
            container = client.containers.run(
                image=self._image,
                command=["python3", "-c", wrapper],
                detach=True,
                mem_limit=self._memory_limit,
                cpu_period=self._cpu_period,
                cpu_quota=self._cpu_quota,
                network_disabled=not self._network_enabled,
                read_only=True,
                tmpfs={"/tmp": "size=64m"},
                volumes={},
                labels={"agent-engine-plugin": "true"},
            )

            result = container.wait(timeout=self._timeout)
            logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")

            duration_ms = (time.time() - start) * 1000

            if result.get("StatusCode") == 0:
                try:
                    output = json.loads(logs.strip().split("\n")[-1])
                except (json.JSONDecodeError, IndexError):
                    output = logs.strip()
                return PluginExecutionResult(
                    success=True,
                    output=output,
                    duration_ms=duration_ms,
                    exit_code=0,
                )
            else:
                return PluginExecutionResult(
                    success=False,
                    error=logs[:2000],
                    duration_ms=duration_ms,
                    exit_code=result.get("StatusCode", -1),
                    logs=logs,
                )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error_msg = str(e)
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                error_msg = f"Container execution timed out after {self._timeout}s"
            return PluginExecutionResult(
                success=False,
                error=error_msg,
                duration_ms=duration_ms,
            )
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception as e:
                    logger.warning("Failed to remove plugin container %s: %s", container.id, e)

    def _build_wrapper(self, code: str, entry_point: str, params: dict, config: dict) -> str:
        params_json = json.dumps(params, ensure_ascii=False)
        config_json = json.dumps(config, ensure_ascii=False)
        return f'''
import json, sys
try:
    exec(compile({code!r}, "<plugin>", "exec"))
    func = locals().get("{entry_point}")
    if func is None:
        print(json.dumps({{"error": "Entry point '{entry_point}' not found"}}))
        sys.exit(1)
    result = func(**json.loads({params_json}))
    print(json.dumps(result, ensure_ascii=False, default=str))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
    sys.exit(1)
'''


def create_sandbox(backend: str = "subprocess", **kwargs) -> Union[PluginSandbox, DockerPluginSandbox]:
    """Create a sandbox instance. Backend: 'subprocess' or 'docker'."""
    if backend == "docker":
        return DockerPluginSandbox(**kwargs)
    return PluginSandbox(**kwargs)
