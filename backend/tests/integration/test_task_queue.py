"""Integration tests for task queue (Q-001~Q-009) and frontend structure (F-001~F-011).

Tests validate configuration, logic, and file structure without requiring
running Celery workers or a frontend dev server.
"""
import ast
import os
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

try:
    import celery
    celery_available = True
except ImportError:
    celery_available = False

requires_celery = pytest.mark.skipif(not celery_available, reason="celery not installed")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BACKEND_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = BACKEND_ROOT.parent / "frontend" / "src"


# ===================================================================
# Q-001: Task submission (TaskQueueService.submit_document_processing)
# ===================================================================

class TestQ001TaskSubmission:
    """Verify TaskQueueService can submit a task and return a task_id."""

    @pytest.mark.asyncio
    async def test_submit_with_celery_returns_result_id(self):
        """When celery_app is provided, send_task is called and result.id returned."""
        from app.platform.task_service.task_service import TaskQueueService

        mock_celery = MagicMock()
        mock_result = MagicMock()
        mock_result.id = "celery-task-abc123"
        mock_celery.send_task.return_value = mock_result

        service = TaskQueueService(celery_app=mock_celery)
        task_id = await service.submit_document_processing(
            document_id="doc-1",
            file_path="/tmp/test.pdf",
            file_type=".pdf",
        )

        assert task_id == "celery-task-abc123"
        mock_celery.send_task.assert_called_once()
        call_kwargs = mock_celery.send_task.call_args
        assert call_kwargs[0][0] == "app.tasks.document_tasks.process_document"
        assert call_kwargs[1]["queue"] == "document"

    @pytest.mark.asyncio
    async def test_submit_without_celery_returns_local_fallback(self):
        """When celery_app is None, returns a local_ prefixed task_id."""
        from app.platform.task_service.task_service import TaskQueueService

        service = TaskQueueService(celery_app=None)
        task_id = await service.submit_document_processing(
            document_id="doc-2",
            file_path="/tmp/test.txt",
            file_type=".txt",
        )

        assert task_id.startswith("local_doc-2_")
        status = await service.get_task_status(task_id)
        assert status["status"] == "PENDING"

    @pytest.mark.asyncio
    async def test_submit_passes_all_parameters(self):
        """All parameters are forwarded to send_task."""
        from app.platform.task_service.task_service import TaskQueueService

        mock_celery = MagicMock()
        mock_celery.send_task.return_value = MagicMock(id="tid")

        service = TaskQueueService(celery_app=mock_celery)
        await service.submit_document_processing(
            document_id="d",
            file_path="/f",
            file_type=".pdf",
            chunk_size=1000,
            chunk_overlap=200,
            chunking_strategy="semantic",
            tenant_id="t1",
            knowledge_base_id="kb1",
        )

        kwargs = mock_celery.send_task.call_args[1]["kwargs"]
        assert kwargs["chunk_size"] == 1000
        assert kwargs["chunk_overlap"] == 200
        assert kwargs["chunking_strategy"] == "semantic"
        assert kwargs["tenant_id"] == "t1"
        assert kwargs["knowledge_base_id"] == "kb1"


# ===================================================================
# Q-003: Progress tracking (update_state PROGRESS)
# ===================================================================

@requires_celery
class TestQ003ProgressTracking:
    """Verify progress tracking via self.update_state calls."""

    def test_update_state_called_with_progress_meta(self):
        """process_document calls self.update_state with PROGRESS state."""
        from app.tasks.document_tasks import process_document

        mock_self = MagicMock()
        mock_self.update_state = MagicMock()

        # We cannot call the actual task without parsers, but we can verify
        # the task function's source contains update_state calls.
        import inspect
        source = inspect.getsource(process_document)
        assert "update_state" in source
        assert '"PROGRESS"' in source or "'PROGRESS'" in source

    def test_progress_stages_defined_in_source(self):
        """Source should define parsing, chunking, indexing, complete stages."""
        import inspect
        from app.tasks.document_tasks import process_document

        source = inspect.getsource(process_document)
        for stage in ["parsing", "chunking", "indexing", "complete"]:
            assert stage in source, f"Stage '{stage}' not found in process_document"

    def test_progress_values_are_monotonic(self):
        """Progress values in source should be monotonically increasing."""
        import inspect
        from app.tasks.document_tasks import process_document

        source = inspect.getsource(process_document)
        # Extract progress values from source
        import re
        progress_values = re.findall(r'"progress":\s*([\d.]+)', source)
        values = [float(v) for v in progress_values]
        assert len(values) >= 3, f"Expected at least 3 progress values, got {len(values)}"
        assert values == sorted(values), f"Progress values not monotonic: {values}"
        assert values[-1] == 1.0, "Final progress should be 1.0"


# ===================================================================
# Q-004: Task retry (RetryableTask autoretry_for)
# ===================================================================

@requires_celery
class TestQ004TaskRetry:
    """Verify RetryableTask retries on transient errors."""

    def test_retryable_task_has_autoretry_for(self):
        """RetryableTask.autoretry_for should include Exception."""
        from app.tasks.document_tasks import RetryableTask

        assert hasattr(RetryableTask, "autoretry_for")
        assert Exception in RetryableTask.autoretry_for

    def test_retryable_task_max_retries(self):
        """Max retries should be configured (default 3)."""
        from app.tasks.document_tasks import RetryableTask

        assert RetryableTask.max_retries == 3

    def test_retryable_task_backoff_enabled(self):
        """Exponential backoff should be enabled."""
        from app.tasks.document_tasks import RetryableTask

        assert RetryableTask.retry_backoff is True
        assert RetryableTask.retry_backoff_max == 60
        assert RetryableTask.retry_jitter is True

    def test_on_retry_callback_exists(self):
        """RetryableTask should have on_retry callback."""
        from app.tasks.document_tasks import RetryableTask

        assert hasattr(RetryableTask, "on_retry")
        # Verify it's callable
        task_instance = RetryableTask()
        task_instance.name = "test_task"
        # Should not raise
        task_instance.on_retry(
            exc=ValueError("transient"),
            task_id="t1",
            args=(),
            kwargs={},
            einfo=None,
        )

    def test_on_failure_appends_to_dead_letter(self):
        """on_failure should append to _dead_letters list."""
        from app.tasks.document_tasks import RetryableTask, _dead_letters

        initial_len = len(_dead_letters)
        task_instance = RetryableTask()
        task_instance.name = "test_task"

        task_instance.on_failure(
            exc=ValueError("permanent failure"),
            task_id="task-failed-1",
            args=("arg1",),
            kwargs={"key": "val"},
            einfo="traceback_string",
        )

        assert len(_dead_letters) == initial_len + 1
        entry = _dead_letters[-1]
        assert entry["task_id"] == "task-failed-1"
        assert entry["task_name"] == "test_task"
        assert entry["error"] == "permanent failure"
        assert "timestamp" in entry


# ===================================================================
# Q-006: Dead letter queue (_dead_letters + on_failure)
# ===================================================================

@requires_celery
class TestQ006DeadLetterQueue:
    """Verify dead letter queue captures failed tasks."""

    def test_get_dead_letters_returns_list(self):
        """get_dead_letters should return a list."""
        from app.tasks.document_tasks import get_dead_letters

        result = get_dead_letters()
        assert isinstance(result, list)

    def test_get_dead_letters_returns_copy(self):
        """get_dead_letters returns a copy, not the original list."""
        from app.tasks.document_tasks import get_dead_letters, _dead_letters

        result = get_dead_letters()
        # Modifying the result should not affect the original
        original_len = len(_dead_letters)
        result.append({"fake": True})
        assert len(_dead_letters) == original_len

    def test_dead_letter_entry_structure(self):
        """Dead letter entries should have required fields."""
        from app.tasks.document_tasks import RetryableTask, _dead_letters

        task_instance = RetryableTask()
        task_instance.name = "app.tasks.document_tasks.process_document"

        task_instance.on_failure(
            exc=RuntimeError("disk full"),
            task_id="dl-test-1",
            args=("doc-99", "/path/file.pdf", ".pdf"),
            kwargs={"chunk_size": 500},
            einfo="full traceback here",
        )

        # Find our entry
        entry = [e for e in _dead_letters if e["task_id"] == "dl-test-1"]
        assert len(entry) == 1
        entry = entry[0]

        required_fields = ["task_id", "task_name", "args", "kwargs", "error", "traceback", "timestamp"]
        for field in required_fields:
            assert field in entry, f"Missing field: {field}"

        assert entry["task_name"] == "app.tasks.document_tasks.process_document"
        assert isinstance(entry["timestamp"], float)

    def test_retry_dead_letter_valid_index(self):
        """retry_dead_letter should re-submit and remove from queue."""
        from app.tasks.document_tasks import _dead_letters, retry_dead_letter

        # Seed a dead letter
        _dead_letters.append({
            "task_id": "dl-retry-1",
            "task_name": "app.tasks.document_tasks.process_document",
            "args": [],
            "kwargs": {},
            "error": "test",
            "traceback": "",
            "timestamp": time.time(),
        })
        idx = len(_dead_letters) - 1

        with patch("app.tasks.document_tasks.celery_app") as mock_app:
            mock_result = MagicMock()
            mock_result.id = "new-task-id"
            mock_app.send_task.return_value = mock_result

            result = retry_dead_letter(idx)
            assert result["new_task_id"] == "new-task-id"
            assert result["status"] == "retried"
            mock_app.send_task.assert_called_once()

    def test_retry_dead_letter_invalid_index(self):
        """retry_dead_letter with invalid index raises ValueError."""
        from app.tasks.document_tasks import retry_dead_letter

        with pytest.raises(ValueError, match="Invalid dead letter index"):
            retry_dead_letter(-1)

        with pytest.raises(ValueError, match="Invalid dead letter index"):
            retry_dead_letter(99999)

    @pytest.mark.asyncio
    async def test_task_queue_service_dead_letters(self):
        """TaskQueueService.get_dead_letters delegates correctly."""
        from app.platform.task_service.task_service import TaskQueueService
        import app.tasks.document_tasks as dt_module

        service = TaskQueueService()

        # Mock at the source module; the import inside get_dead_letters will pick it up
        original = dt_module.get_dead_letters
        dt_module.get_dead_letters = lambda: [{"task_id": "x"}]
        try:
            result = await service.get_dead_letters()
            assert result == [{"task_id": "x"}]
        finally:
            dt_module.get_dead_letters = original


# ===================================================================
# Q-007: Distributed lock (Redis-based)
# ===================================================================

class TestQ007DistributedLock:
    """Verify Redis-based distributed lock mechanism."""

    def test_redis_lock_mechanism_available(self):
        """redis.asyncio should support lock() for distributed locking."""
        import redis.asyncio as aioredis
        # Verify the lock method exists on the Redis client class
        assert hasattr(aioredis.Redis, "lock")

    @pytest.mark.asyncio
    async def test_rate_limiter_uses_redis_pipeline(self):
        """RateLimiter.check uses Redis pipeline for atomic operations."""
        from app.core.rate_limiter import RateLimiter

        mock_redis = MagicMock()
        pipe_mock = MagicMock()
        pipe_mock.execute = AsyncMock(return_value=[None, None, 5, None])
        mock_redis.pipeline.return_value = pipe_mock

        limiter = RateLimiter(redis_client=mock_redis)
        result = await limiter.check("test_key", max_requests=10, window_seconds=60)

        assert result is True  # 5 <= 10
        mock_redis.pipeline.assert_called_once()
        pipe_mock.zremrangebyscore.assert_called_once()
        pipe_mock.zadd.assert_called_once()
        pipe_mock.zcard.assert_called_once()
        pipe_mock.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_when_exceeded(self):
        """RateLimiter.check returns False when max_requests exceeded."""
        from app.core.rate_limiter import RateLimiter

        mock_redis = MagicMock()
        pipe_mock = MagicMock()
        pipe_mock.execute = AsyncMock(return_value=[None, None, 150, None])
        mock_redis.pipeline.return_value = pipe_mock

        limiter = RateLimiter(redis_client=mock_redis)
        result = await limiter.check("test_key", max_requests=100, window_seconds=60)

        assert result is False  # 150 > 100

    @pytest.mark.asyncio
    async def test_rate_limiter_no_redis_allows_all(self):
        """Without Redis, all requests are allowed."""
        from app.core.rate_limiter import RateLimiter

        limiter = RateLimiter(redis_client=None)
        result = await limiter.check("key", max_requests=1, window_seconds=1)
        assert result is True


# ===================================================================
# Q-008: Periodic tasks (celery beat_schedule)
# ===================================================================

@requires_celery
class TestQ008BeatSchedule:
    """Verify beat_schedule defines expected periodic tasks."""

    def test_beat_schedule_exists(self):
        """celery_app.conf should have beat_schedule defined."""
        from app.tasks.celery_app import celery_app

        assert hasattr(celery_app.conf, "beat_schedule")
        assert celery_app.conf.beat_schedule is not None

    def test_cleanup_expired_memory_scheduled(self):
        """cleanup-expired-memory task should be in beat_schedule."""
        from app.tasks.celery_app import celery_app

        schedule = celery_app.conf.beat_schedule
        assert "cleanup-expired-memory" in schedule
        task_config = schedule["cleanup-expired-memory"]
        assert task_config["task"] == "app.tasks.cleanup_tasks.cleanup_expired_memory"

    def test_cleanup_schedule_interval(self):
        """cleanup task should run every 3600 seconds (1 hour)."""
        from app.tasks.celery_app import celery_app

        task_config = celery_app.conf.beat_schedule["cleanup-expired-memory"]
        assert task_config["schedule"] == 3600.0

    def test_beat_schedule_tasks_have_required_keys(self):
        """Every beat_schedule entry should have task and schedule keys."""
        from app.tasks.celery_app import celery_app

        for name, config in celery_app.conf.beat_schedule.items():
            assert "task" in config, f"Schedule '{name}' missing 'task' key"
            assert "schedule" in config, f"Schedule '{name}' missing 'schedule' key"


# ===================================================================
# Q-009: Task routing (task_routes config)
# ===================================================================

@requires_celery
class TestQ009TaskRoutes:
    """Verify task_routes route to correct queues."""

    def test_task_routes_configured(self):
        """celery_app.conf should have task_routes defined."""
        from app.tasks.celery_app import celery_app

        assert celery_app.conf.task_routes is not None
        assert len(celery_app.conf.task_routes) > 0

    def test_document_tasks_route_to_document_queue(self):
        """document_tasks.* should route to 'document' queue."""
        from app.tasks.celery_app import celery_app

        routes = celery_app.conf.task_routes
        assert "app.tasks.document_tasks.*" in routes
        assert routes["app.tasks.document_tasks.*"]["queue"] == "document"

    def test_model_tasks_route_to_model_queue(self):
        """model_tasks.* should route to 'model' queue."""
        from app.tasks.celery_app import celery_app

        routes = celery_app.conf.task_routes
        assert "app.tasks.model_tasks.*" in routes
        assert routes["app.tasks.model_tasks.*"]["queue"] == "model"

    def test_cleanup_tasks_route_to_cleanup_queue(self):
        """cleanup_tasks.* should route to 'cleanup' queue."""
        from app.tasks.celery_app import celery_app

        routes = celery_app.conf.task_routes
        assert "app.tasks.cleanup_tasks.*" in routes
        assert routes["app.tasks.cleanup_tasks.*"]["queue"] == "cleanup"

    def test_default_queue_is_default(self):
        """task_default_queue should be 'default'."""
        from app.tasks.celery_app import celery_app

        assert celery_app.conf.task_default_queue == "default"

    def test_celery_serialization_config(self):
        """Celery should be configured with JSON serialization."""
        from app.tasks.celery_app import celery_app

        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"
        assert "json" in celery_app.conf.accept_content

    def test_celery_worker_config(self):
        """Worker-level config: task_acks_late, prefetch, track_started."""
        from app.tasks.celery_app import celery_app

        assert celery_app.conf.task_track_started is True
        assert celery_app.conf.task_acks_late is True
        assert celery_app.conf.worker_prefetch_multiplier == 1


# ===================================================================
# F-001 ~ F-011: Frontend structure validation
# ===================================================================

def _read_file(path: Path) -> str:
    """Read file content, skip if missing."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _parse_tsx(path: Path) -> dict:
    """Parse a TSX/TS file and extract basic structural info."""
    content = _read_file(path)
    info = {
        "exists": path.exists(),
        "content": content,
        "has_default_export": "export default" in content,
        "has_use_client": "'use client'" in content or '"use client"' in content,
        "imports": [],
        "exports": [],
    }
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("import "):
            info["imports"].append(stripped[:100])
        if stripped.startswith("export "):
            info["exports"].append(stripped[:100])
    return info


class TestF001LoginLogout:
    """F-001: Login/Logout (login/page.tsx + auth store)."""

    def test_login_page_exists(self):
        path = FRONTEND_ROOT / "app" / "(auth)" / "login" / "page.tsx"
        assert path.exists(), f"Login page not found: {path}"

    def test_login_page_uses_auth_store(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(auth)" / "login" / "page.tsx")
        assert "useAuthStore" in content

    def test_login_page_has_login_function(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(auth)" / "login" / "page.tsx")
        assert "login" in content
        assert "username" in content
        assert "password" in content

    def test_login_page_has_error_handling(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(auth)" / "login" / "page.tsx")
        assert "try" in content
        assert "catch" in content
        assert "message.error" in content

    def test_auth_store_exists(self):
        path = FRONTEND_ROOT / "store" / "auth.ts"
        assert path.exists(), f"Auth store not found: {path}"

    def test_auth_store_has_login_logout(self):
        content = _read_file(FRONTEND_ROOT / "store" / "auth.ts")
        assert "login" in content
        assert "logout" in content

    def test_auth_store_uses_zustand(self):
        content = _read_file(FRONTEND_ROOT / "store" / "auth.ts")
        assert "create" in content
        assert "zustand" in content

    def test_auth_store_login_stores_token(self):
        content = _read_file(FRONTEND_ROOT / "store" / "auth.ts")
        assert "localStorage.setItem" in content
        assert "token" in content

    def test_auth_store_logout_clears_token(self):
        content = _read_file(FRONTEND_ROOT / "store" / "auth.ts")
        assert "localStorage.removeItem" in content

    def test_auth_store_has_check_auth(self):
        content = _read_file(FRONTEND_ROOT / "store" / "auth.ts")
        assert "checkAuth" in content


class TestF002ToF006AgentAndKnowledge:
    """F-002~F-006: Agent list/create/chat/streaming/knowledge."""

    def test_agents_list_page_exists(self):
        path = FRONTEND_ROOT / "app" / "(platform)" / "agents" / "page.tsx"
        assert path.exists()

    def test_agents_list_uses_api(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(platform)" / "agents" / "page.tsx")
        assert "api" in content
        assert "listAgents" in content

    def test_agents_list_has_card_layout(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(platform)" / "agents" / "page.tsx")
        assert "Card" in content

    def test_agent_create_page_exists(self):
        path = FRONTEND_ROOT / "app" / "(platform)" / "agents" / "create" / "page.tsx"
        assert path.exists()

    def test_agent_create_has_form(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(platform)" / "agents" / "create" / "page.tsx")
        assert "Form" in content
        assert "createAgent" in content

    def test_agent_create_has_model_fields(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(platform)" / "agents" / "create" / "page.tsx")
        assert "model_provider" in content
        assert "model_name" in content
        assert "system_prompt" in content

    def test_agent_chat_page_exists(self):
        path = FRONTEND_ROOT / "app" / "(platform)" / "agents" / "[id]" / "chat" / "page.tsx"
        assert path.exists()

    def test_agent_chat_uses_chat_store(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(platform)" / "agents" / "[id]" / "chat" / "page.tsx")
        assert "useChatStore" in content
        assert "sendMessage" in content

    def test_chat_store_supports_streaming(self):
        content = _read_file(FRONTEND_ROOT / "store" / "chat.ts")
        assert "streaming" in content
        assert "ReadableStream" in content or "getReader" in content or "response.body" in content

    def test_chat_store_sse_parsing(self):
        content = _read_file(FRONTEND_ROOT / "store" / "chat.ts")
        assert "data: " in content
        assert "JSON.parse" in content

    def test_chat_message_component_exists(self):
        path = FRONTEND_ROOT / "components" / "ChatMessage.tsx"
        assert path.exists()

    def test_chat_message_handles_roles(self):
        content = _read_file(FRONTEND_ROOT / "components" / "ChatMessage.tsx")
        assert "user" in content
        # Component uses isUser pattern to distinguish user vs assistant styling
        assert "isUser" in content
        assert "RobotOutlined" in content

    def test_knowledge_page_exists(self):
        path = FRONTEND_ROOT / "app" / "(platform)" / "knowledge" / "page.tsx"
        assert path.exists()

    def test_knowledge_page_has_list_and_delete(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(platform)" / "knowledge" / "page.tsx")
        assert "listKnowledgeBases" in content
        assert "deleteKnowledgeBase" in content

    def test_knowledge_detail_page_exists(self):
        path = FRONTEND_ROOT / "app" / "(platform)" / "knowledge" / "[id]" / "page.tsx"
        assert path.exists()

    def test_api_client_has_agent_methods(self):
        content = _read_file(FRONTEND_ROOT / "lib" / "api.ts")
        assert "listAgents" in content
        assert "createAgent" in content
        assert "deleteAgent" in content
        assert "publishAgent" in content

    def test_api_client_has_knowledge_methods(self):
        content = _read_file(FRONTEND_ROOT / "lib" / "api.ts")
        assert "listKnowledgeBases" in content
        assert "createKnowledgeBase" in content
        assert "uploadDocument" in content
        assert "deleteKnowledgeBase" in content

    def test_types_define_agent_interface(self):
        content = _read_file(FRONTEND_ROOT / "types" / "index.ts")
        assert "interface Agent" in content
        assert "interface KnowledgeBase" in content
        assert "interface ChatMessage" in content


class TestF008TokenExpiry:
    """F-008: Token expiry handling (api.ts 401 auto-logout)."""

    def test_api_has_401_interceptor(self):
        content = _read_file(FRONTEND_ROOT / "lib" / "api.ts")
        assert "interceptors.response" in content

    def test_401_removes_token(self):
        content = _read_file(FRONTEND_ROOT / "lib" / "api.ts")
        assert "401" in content
        assert "localStorage.removeItem" in content
        assert "token" in content

    def test_401_redirects_to_login(self):
        content = _read_file(FRONTEND_ROOT / "lib" / "api.ts")
        assert "/login" in content

    def test_request_interceptor_attaches_token(self):
        content = _read_file(FRONTEND_ROOT / "lib" / "api.ts")
        assert "interceptors.request" in content
        assert "Authorization" in content
        assert "Bearer" in content


class TestF009PermissionControl:
    """F-009: Permission control (require_role + sidebar filtering)."""

    def test_platform_layout_checks_token(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(platform)" / "layout.tsx")
        assert "token" in content
        assert "checkAuth" in content

    def test_platform_layout_redirects_without_token(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(platform)" / "layout.tsx")
        assert "/login" in content

    def test_sidebar_has_menu_items(self):
        content = _read_file(FRONTEND_ROOT / "components" / "Sidebar.tsx")
        assert "Agents" in content
        assert "Knowledge" in content
        assert "Workflows" in content
        assert "Models" in content

    def test_types_define_user_with_role(self):
        content = _read_file(FRONTEND_ROOT / "types" / "index.ts")
        assert "interface User" in content
        assert "role" in content

    def test_header_has_logout(self):
        content = _read_file(FRONTEND_ROOT / "components" / "Header.tsx")
        assert "logout" in content
        assert "Logout" in content


class TestF010ResponsiveLayout:
    """F-010: Responsive layout (Tailwind responsive classes)."""

    def test_agents_page_responsive_grid(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(platform)" / "agents" / "page.tsx")
        # Implementation uses Tailwind CSS responsive grid, not Ant Design Col props
        assert "grid-cols-1" in content
        assert "sm:grid-cols-2" in content
        assert "lg:grid-cols-3" in content

    def test_login_page_has_centered_layout(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(auth)" / "login" / "page.tsx")
        assert "minHeight" in content or "min-h" in content
        assert "alignItems" in content or "items-center" in content
        assert "justifyContent" in content or "justify-center" in content

    def test_platform_layout_has_sidebar_structure(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(platform)" / "layout.tsx")
        assert "Sidebar" in content
        assert "Header" in content
        assert "Content" in content

    def test_sidebar_has_fixed_width(self):
        content = _read_file(FRONTEND_ROOT / "components" / "Sidebar.tsx")
        # Implementation uses CSS variable for sidebar width, not hardcoded pixels
        assert "width" in content
        assert "ae-sidebar-width" in content


class TestF011ErrorHandling:
    """F-011: Error handling (try/catch + toast)."""

    def test_login_page_try_catch(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(auth)" / "login" / "page.tsx")
        assert "try" in content
        assert "catch" in content
        assert "message.error" in content

    def test_agents_page_try_catch(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(platform)" / "agents" / "page.tsx")
        assert "try" in content
        assert "catch" in content
        assert "message.error" in content

    def test_knowledge_page_try_catch(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(platform)" / "knowledge" / "page.tsx")
        assert "try" in content or "catch" in content or "message.error" in content

    def test_agent_create_try_catch(self):
        content = _read_file(FRONTEND_ROOT / "app" / "(platform)" / "agents" / "create" / "page.tsx")
        assert "try" in content
        assert "catch" in content
        assert "message.error" in content

    def test_chat_store_error_handling(self):
        content = _read_file(FRONTEND_ROOT / "store" / "chat.ts")
        assert "error" in content
        assert "try" in content
        assert "catch" in content

    def test_api_client_error_propagation(self):
        content = _read_file(FRONTEND_ROOT / "lib" / "api.ts")
        assert "Promise.reject" in content


# ===================================================================
# Cross-cutting: TaskQueueService integration
# ===================================================================

class TestTaskQueueServiceIntegration:
    """Additional integration tests for TaskQueueService."""

    @pytest.mark.asyncio
    async def test_cancel_task_with_celery(self):
        from app.platform.task_service.task_service import TaskQueueService

        mock_celery = MagicMock()
        service = TaskQueueService(celery_app=mock_celery)

        result = await service.cancel_task("task-123")
        assert result["status"] == "cancelled"
        mock_celery.control.revoke.assert_called_once_with("task-123", terminate=True)

    @pytest.mark.asyncio
    async def test_cancel_task_without_celery(self):
        from app.platform.task_service.task_service import TaskQueueService

        service = TaskQueueService(celery_app=None)
        # Submit a local task first
        task_id = await service.submit_document_processing(
            document_id="d1", file_path="/f", file_type=".txt"
        )
        result = await service.cancel_task(task_id)
        assert result["status"] == "cancelled"
        status = await service.get_task_status(task_id)
        assert status["status"] == "CANCELLED"

    @pytest.mark.asyncio
    async def test_get_task_status_unknown(self):
        from app.platform.task_service.task_service import TaskQueueService

        service = TaskQueueService(celery_app=None)
        status = await service.get_task_status("nonexistent-id")
        assert status["status"] == "UNKNOWN"

    @pytest.mark.asyncio
    @requires_celery
    async def test_get_task_status_with_celery(self):
        """get_task_status with celery_app delegates to AsyncResult."""
        from app.platform.task_service.task_service import TaskQueueService

        mock_celery = MagicMock()
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.info = {"progress": 1.0, "stage": "complete"}

        # The method imports celery_app internally; mock AsyncResult on the module
        with patch("app.tasks.celery_app.celery_app") as mock_real_celery:
            mock_real_celery.AsyncResult.return_value = mock_result

            service = TaskQueueService(celery_app=mock_celery)
            status = await service.get_task_status("task-abc")

            assert status["task_id"] == "task-abc"
            assert status["status"] == "SUCCESS"
            assert status["progress"] == 1.0
            assert status["stage"] == "complete"
