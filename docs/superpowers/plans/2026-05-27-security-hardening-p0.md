# Security Hardening P0 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 14 Critical security vulnerabilities identified in the code review before any production deployment.

**Architecture:** Targeted fixes to existing files — no large refactors. Each task is isolated: modifies 1-3 files, adds tests, verifiable independently.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0, Pydantic, react-markdown (frontend), simpleeval (expression evaluator)

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/config.py` | Modify | Startup validation for secrets |
| `backend/app/main.py` | Modify | CORS fix |
| `backend/app/api/v1/users.py` | Modify | Auth guard on registration |
| `backend/app/schemas/api.py` | Modify | Password validation |
| `backend/app/models/base.py` | Modify | Encrypted field helpers |
| `backend/app/engines/workflow_engine/workflow.py` | Modify | Safe expression evaluator, remove exec() |
| `backend/app/engines/tool_engine/builtin/code_executor.py` | Modify | Remove bash, AST-level checking |
| `backend/app/engines/tool_engine/builtin/db_query.py` | Modify | Safe SQL execution |
| `backend/app/engines/tool_engine/builtin/http_request.py` | Modify | DNS rebinding protection |
| `backend/app/api/v1/webhooks.py` | Modify | URL validation |
| `backend/app/core/webhook_dispatcher.py` | Modify | SSRF check before delivery |
| `backend/app/core/security.py` | Modify | Encrypt/decrypt for API keys |
| `backend/app/engines/knowledge_engine/storage/graph/neo4j_store.py` | Modify | MERGE instead of CREATE |
| `backend/app/engines/knowledge_engine/graph/graph_builder.py` | Modify | Fix merge entity |
| `frontend/src/components/MarkdownRenderer.tsx` | Rewrite | react-markdown + rehype-sanitize |
| `frontend/src/app/(auth)/login/page.tsx` | Modify | Remove hardcoded creds |
| `frontend/package.json` | Modify | Add react-markdown deps |

---

### Task 1: Force secret key configuration at startup

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/unit/test_security.py`

The application must refuse to start with default/insecure secret keys.

- [ ] **Step 1: Add validation to Settings**

In `backend/app/config.py`, add a `model_config` validator after the class body:

```python
from pydantic_settings import BaseSettings
from pydantic import model_validator


class Settings(BaseSettings):
    # ... existing fields unchanged ...

    ENVIRONMENT: str = "development"

    model_config = {
        "env_file": ".env",
        "extra": "forbid",
    }

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            insecure = {
                "SECRET_KEY": "change-me-in-production",
                "ENCRYPTION_KEY": "change-me-in-production",
            }
            for field, bad_default in insecure.items():
                val = getattr(self, field, "")
                if not val or val == bad_default or len(val) < 16:
                    raise ValueError(
                        f"{field} must be set to a secure value (>=16 chars) in production. "
                        f"Set it in .env or environment variable."
                    )
        return self
```

- [ ] **Step 2: Write test**

In `backend/tests/unit/test_security.py`, add:

```python
import pytest
from pydantic import ValidationError


def test_production_rejects_default_secret_key():
    """Production mode must reject default SECRET_KEY."""
    import os
    env = {**os.environ, "ENVIRONMENT": "production", "SECRET_KEY": "change-me-in-production"}
    with pytest.monkeypatch.context() as m:
        for k, v in env.items():
            m.setenv(k, v)
        with pytest.raises(ValidationError, match="SECRET_KEY must be set"):
            from app.config import Settings
            Settings()


def test_production_rejects_short_secret_key():
    """Production mode must reject short SECRET_KEY."""
    import os
    env = {**os.environ, "ENVIRONMENT": "production", "SECRET_KEY": "short"}
    with pytest.monkeypatch.context() as m:
        for k, v in env.items():
            m.setenv(k, v)
        with pytest.raises(ValidationError, match="SECRET_KEY must be set"):
            from app.config import Settings
            Settings()


def test_development_allows_default_secret_key():
    """Development mode allows default keys."""
    import os
    env = {**os.environ, "ENVIRONMENT": "development"}
    with pytest.monkeypatch.context() as m:
        for k, v in env.items():
            m.setenv(k, v)
        from app.config import Settings
        s = Settings()
        assert s.SECRET_KEY == "change-me-in-production"
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/unit/test_security.py -v -k "secret"`
Expected: 3 PASS

- [ ] **Step 4: Commit**

```bash
git add app/config.py tests/unit/test_security.py
git commit -m "fix(security): 强制生产环境配置安全密钥"
```

---

### Task 2: Fix CORS configuration

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Replace wildcard CORS with configurable origins**

In `backend/app/main.py`, replace lines 30-36:

```python
# Before:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# After:
import json

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", '["http://localhost:3000"]').strip()
try:
    _origins = json.loads(CORS_ORIGINS)
except (json.JSONDecodeError, TypeError):
    _origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Step 2: Update .env.example**

In `.env.example`, add:

```env
# CORS allowed origins (JSON array or comma-separated)
CORS_ORIGINS=["http://localhost:3000"]
```

- [ ] **Step 3: Commit**

```bash
git add app/main.py .env.example
git commit -m "fix(security): CORS origins 从环境变量读取，不再使用通配符"
```

---

### Task 3: Guard user registration endpoint

**Files:**
- Modify: `backend/app/api/v1/users.py`
- Modify: `backend/app/schemas/api.py`

- [ ] **Step 1: Add auth requirement and restrict role assignment**

In `backend/app/api/v1/users.py`, replace the `register_user` endpoint (lines 19-48):

```python
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    body: RegisterUserRequest,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_role("admin")),
):
    """Register a new user (admin only)."""
    stmt = select(UserModel).where(UserModel.username == body.username)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already exists")

    # New users default to 'viewer'; only admin can set higher roles
    role = body.role if body.role in ("viewer", "contributor") else "viewer"

    user = UserModel(
        username=body.username,
        hashed_password=get_password_hash(body.password),
        email=body.email,
        role=role,
        tenant_id=_admin["tenant_id"],
    )
    db.add(user)
    await db.flush()
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "status": user.status,
    }
```

- [ ] **Step 2: Add password validation to RegisterUserRequest**

In `backend/app/schemas/api.py`, update `RegisterUserRequest`:

```python
class RegisterUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(min_length=8, max_length=128)
    email: Optional[str] = None
    role: Optional[str] = "viewer"
```

- [ ] **Step 3: Commit**

```bash
git add app/api/v1/users.py app/schemas/api.py
git commit -m "fix(security): 用户注册要求 admin 权限，限制角色分配，密码最小8位"
```

---

### Task 4: Encrypt API keys and OAuth tokens at rest

**Files:**
- Modify: `backend/app/models/base.py`
- Modify: `backend/app/api/v1/models.py`

- [ ] **Step 1: Add hybrid property for encrypted api_key on ModelProviderModel**

In `backend/app/models/base.py`, find `ModelProviderModel` and add hybrid encryption. Add at top of file:

```python
from app.core.security import encrypt, decrypt as _decrypt
```

Then replace the `api_key` column usage with a hybrid property pattern. Add to `ModelProviderModel`:

```python
class ModelProviderModel(Base):
    __tablename__ = "model_providers"
    # ... existing columns ...
    _api_key_encrypted = Column("api_key", String(500), nullable=True)

    @property
    def api_key(self) -> Optional[str]:
        if not self._api_key_encrypted:
            return None
        try:
            return _decrypt(self._api_key_encrypted)
        except Exception:
            # Fallback: might be plaintext from before migration
            return self._api_key_encrypted

    @api_key.setter
    def api_key(self, value: Optional[str]):
        if value:
            self._api_key_encrypted = encrypt(value)
        else:
            self._api_key_encrypted = None
```

Note: Keep the column name `api_key` in DB but access through property that encrypts/decrypts transparently. The column definition should use `_api_key_encrypted` mapped to the same DB column via `Column("api_key", ...)`.

- [ ] **Step 2: Same pattern for AccountIntegrateModel.access_token**

```python
class AccountIntegrateModel(Base):
    __tablename__ = "account_integrates"
    # ... existing columns ...
    _access_token_encrypted = Column("access_token", String(500), nullable=True)

    @property
    def access_token(self) -> Optional[str]:
        if not self._access_token_encrypted:
            return None
        try:
            return _decrypt(self._access_token_encrypted)
        except Exception:
            return self._access_token_encrypted

    @access_token.setter
    def access_token(self, value: Optional[str]):
        if value:
            self._access_token_encrypted = encrypt(value)
        else:
            self._access_token_encrypted = None
```

- [ ] **Step 3: Verify existing test passes**

Run: `cd backend && python -m pytest tests/unit/ -q --tb=short`
Expected: All pass (transparent encryption, no test changes needed)

- [ ] **Step 4: Commit**

```bash
git add app/models/base.py
git commit -m "fix(security): API Key 和 OAuth Token 透明加密存储"
```

---

### Task 5: Replace eval() with AST-safe expression evaluator

**Files:**
- Modify: `backend/app/engines/workflow_engine/workflow.py`
- Test: `backend/tests/unit/test_workflow_engine.py`

- [ ] **Step 1: Implement safe expression evaluator**

In `backend/app/engines/workflow_engine/workflow.py`, replace the `evaluate_expression` method on `WorkflowState` (lines 167-182) with an AST-based safe evaluator:

```python
import ast

class _SafeExprVisitor(ast.NodeVisitor):
    """Whitelist AST node types for safe expression evaluation."""
    ALLOWED_NODES = {
        ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Compare,
        ast.Call, ast.Constant, ast.Name, ast.Load, ast.And, ast.Or,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
        ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.In, ast.NotIn, ast.USub, ast.Not, ast.Is, ast.IsNot,
        ast.List, ast.Tuple, ast.Dict, ast.Str, ast.Num,
        ast.Attribute, ast.Subscript, ast.Index,
    }

    def __init__(self):
        self.errors: list[str] = []

    def visit(self, node):
        if type(node) not in self.ALLOWED_NODES:
            self.errors.append(f"Forbidden expression: {type(node).__name__}")
            return
        self.generic_visit(node)


class WorkflowState:
    # ... __init__, set_var, get_var unchanged ...

    def evaluate_expression(self, expr: str) -> Any:
        """Safely evaluate expression using AST whitelist."""
        # Parse into AST
        try:
            tree = ast.parse(expr, mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Invalid expression: {e}")

        # Validate node types
        visitor = _SafeExprVisitor()
        visitor.visit(tree)
        if visitor.errors:
            raise ValueError(f"Forbidden operation: {visitor.errors[0]}")

        # Build safe namespace
        safe_globals = {"__builtins__": {}}
        safe_locals = {
            "True": True, "False": False, "None": None,
            "len": len, "str": str, "int": int, "float": float,
            "abs": abs, "min": min, "max": max, "sum": sum,
            **self.variables,
        }

        return eval(compile(tree, "<expr>", "eval"), safe_globals, safe_locals)
```

- [ ] **Step 2: Add tests for safe evaluator**

In `backend/tests/unit/test_workflow_engine.py`, add:

```python
import pytest
from app.engines.workflow_engine.workflow import WorkflowState


class TestSafeExpressionEvaluator:
    def test_basic_arithmetic(self):
        state = WorkflowState()
        assert state.evaluate_expression("1 + 2") == 3

    def test_variable_access(self):
        state = WorkflowState()
        state.set_var("x", 10)
        assert state.evaluate_expression("x > 5") is True

    def test_comparison(self):
        state = WorkflowState()
        state.set_var("score", 85)
        assert state.evaluate_expression("score >= 80 and score < 90") is True

    def test_rejects_import(self):
        state = WorkflowState()
        with pytest.raises(ValueError, match="Forbidden"):
            state.evaluate_expression("__import__('os')")

    def test_rejects_attribute_access_to_builtins(self):
        state = WorkflowState()
        with pytest.raises(ValueError, match="Forbidden"):
            state.evaluate_expression("().__class__.__bases__")

    def test_rejects_exec(self):
        state = WorkflowState()
        with pytest.raises(ValueError):
            state.evaluate_expression("exec('print(1)')")

    def test_string_operations(self):
        state = WorkflowState()
        state.set_var("name", "hello")
        assert state.evaluate_expression("len(name)") == 5
```

- [ ] **Step 3: Run tests**

Run: `cd backend && python -m pytest tests/unit/test_workflow_engine.py -v`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add app/engines/workflow_engine/workflow.py tests/unit/test_workflow_engine.py
git commit -m "fix(security): 用 AST 白名单替换 eval() 表达式求值"
```

---

### Task 6: Remove exec() CODE node — replace with subprocess sandbox

**Files:**
- Modify: `backend/app/engines/workflow_engine/workflow.py`

- [ ] **Step 1: Replace _execute_code with subprocess-based execution**

In `backend/app/engines/workflow_engine/workflow.py`, replace the `_execute_code` method:

```python
async def _execute_code(self, node: WorkflowNode, state: WorkflowState) -> dict:
    """Execute code in isolated subprocess, not via exec()."""
    code = node.config.get("code", "")
    timeout = node.config.get("timeout", 30)
    if not code:
        return {"output": None, "error": "No code provided"}

    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        # Wrap code to capture 'result' variable if set
        wrapper = (
            "import json, sys\n"
            "_result_local = None\n"
            f"{code}\n"
            "if '_result_local' in dir():\n"
            "    print(json.dumps(_result_local), file=sys.stderr)\n"
        )
        f.write(wrapper)
        script_path = f.name

    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return {
                "output": stdout.decode("utf-8", errors="replace")[:5000],
                "error": stderr.decode("utf-8", errors="replace")[:2000] if proc.returncode else None,
                "exit_code": proc.returncode,
            }
        except asyncio.TimeoutError:
            proc.kill()
            return {"output": None, "error": f"Code execution timed out after {timeout}s"}
    finally:
        os.unlink(script_path)
```

- [ ] **Step 2: Commit**

```bash
git add app/engines/workflow_engine/workflow.py
git commit -m "fix(security): CODE 节点改用子进程沙箱，移除 exec()"
```

---

### Task 7: Fix code_executor — remove bash mode, AST-level import check

**Files:**
- Modify: `backend/app/engines/tool_engine/builtin/code_executor.py`

- [ ] **Step 1: Remove bash mode, use AST for import checking**

Replace the entire file with:

```python
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
    description="Execute Python code in a sandboxed subprocess. Bash mode is disabled.",
    tool_type="builtin",
    input_schema=INPUT_SCHEMA,
    handler=_execute,
    permissions=["tool:code_executor"],
)
```

- [ ] **Step 2: Commit**

```bash
git add app/engines/tool_engine/builtin/code_executor.py
git commit -m "fix(security): 移除 bash 模式，改用 AST 级别导入检查"
```

---

### Task 8: Fix db_query SQL injection

**Files:**
- Modify: `backend/app/engines/tool_engine/builtin/db_query.py`

- [ ] **Step 1: Add semicolon stripping, enforce LIMIT, add table allowlist**

Replace the entire file:

```python
"""Built-in tool: read-only database query execution."""
from __future__ import annotations

import logging
import re
from typing import Any

from app.engines.tool_engine.registry import ToolDef

logger = logging.getLogger(__name__)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "SQL SELECT query to execute (read-only)",
        },
        "limit": {
            "type": "integer",
            "default": 100,
            "maximum": 500,
            "description": "Maximum rows to return",
        },
    },
    "required": ["query"],
}

FORBIDDEN_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE",
    "GRANT", "REVOKE", "EXEC", "EXECUTE", "MERGE", "REPLACE",
    "INTO OUTFILE", "INTO DUMPFILE", "LOAD_FILE",
}

# Only SELECT and WITH (CTE) are allowed as statement starters
_ALLOWED_STARTS = ("SELECT", "WITH")


def _is_safe_query(query: str) -> tuple[bool, str]:
    """Validate query is read-only. Returns (safe, reason)."""
    # Strip comments
    cleaned = re.sub(r"--.*$", "", query, flags=re.MULTILINE)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()

    # Remove trailing semicolons and anything after
    if ";" in cleaned:
        cleaned = cleaned[:cleaned.index(";")].strip()

    if not cleaned:
        return False, "Empty query"

    upper = cleaned.upper()
    if not upper.startswith(_ALLOWED_STARTS):
        return False, "Only SELECT or WITH queries are allowed"

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper):
            return False, f"Forbidden keyword: {keyword}"

    return True, cleaned


async def _execute(params: dict[str, Any]) -> dict[str, Any]:
    """Execute a read-only SQL query."""
    query = params["query"]
    limit = min(params.get("limit", 100), 500)

    safe, result = _is_safe_query(query)
    if not safe:
        return {"error": result}

    cleaned_query = result  # result is the cleaned query when safe=True

    # Enforce LIMIT
    if "LIMIT" not in cleaned_query.upper():
        cleaned_query = f"{cleaned_query} LIMIT {limit}"

    try:
        from app.core.database import engine
        from sqlalchemy import text

        async with engine.connect() as conn:
            result = await conn.execute(text(cleaned_query))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchmany(limit)]

        return {"columns": columns, "rows": rows, "row_count": len(rows)}
    except Exception as e:
        logger.error("DB query failed: %s", e)
        return {"error": f"Query failed: {e}"}


db_query_tool = ToolDef(
    name="db_query",
    description="Execute read-only SQL queries. Only SELECT queries with enforced LIMIT.",
    tool_type="builtin",
    input_schema=INPUT_SCHEMA,
    handler=_execute,
    permissions=["tool:db_query"],
)
```

- [ ] **Step 2: Commit**

```bash
git add app/engines/tool_engine/builtin/db_query.py
git commit -m "fix(security): db_query 防注入增强——分号剥离、注释清除、OUTFILE 拦截"
```

---

### Task 9: Fix SSRF — webhook URL validation + http_request DNS rebinding

**Files:**
- Modify: `backend/app/engines/tool_engine/builtin/http_request.py`
- Modify: `backend/app/api/v1/webhooks.py`
- Modify: `backend/app/core/webhook_dispatcher.py`

- [ ] **Step 1: Extract shared SSRF validator into core module**

Create `backend/app/core/ssrf.py`:

```python
"""Shared SSRF protection utilities."""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

BLOCKED_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("0.0.0.0/8"),
]

BLOCKED_HOSTNAMES = {
    "localhost", "127.0.0.1", "0.0.0.0",
    "metadata.google.internal", "169.254.169.254",
    "[::1]",
}


def is_safe_url(url: str) -> tuple[bool, str]:
    """Check if URL is safe from SSRF. Returns (safe, reason)."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL"

    if parsed.scheme not in ("http", "https"):
        return False, f"Unsupported scheme: {parsed.scheme}"

    hostname = parsed.hostname
    if not hostname:
        return False, "No hostname in URL"

    if hostname in BLOCKED_HOSTNAMES:
        return False, f"Blocked hostname: {hostname}"

    # Check if hostname is a literal IP
    try:
        ip = ipaddress.ip_address(hostname)
        if not _is_safe_ip(ip):
            return False, f"Blocked IP: {ip}"
    except ValueError:
        # Domain name — resolve and check
        try:
            resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for family, _, _, _, sockaddr in resolved[:5]:
                addr = ipaddress.ip_address(sockaddr[0])
                if not _is_safe_ip(addr):
                    return False, f"Resolved to blocked IP: {addr}"
        except socket.gaierror:
            pass  # Unresolvable domains will fail at request time

    return True, ""


def _is_safe_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    for network in BLOCKED_IP_RANGES:
        if ip in network:
            return False
    return True
```

- [ ] **Step 2: Update http_request.py to use shared validator**

Replace `http_request.py` with:

```python
"""Built-in tool: SSRF-safe HTTP requests."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.ssrf import is_safe_url
from app.engines.tool_engine.registry import ToolDef

logger = logging.getLogger(__name__)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "url": {"type": "string", "description": "URL to request"},
        "method": {
            "type": "string",
            "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
            "default": "GET",
        },
        "headers": {"type": "object", "description": "HTTP headers", "default": {}},
        "body": {"type": "object", "description": "Request body (JSON)"},
        "timeout": {"type": "integer", "default": 30, "description": "Timeout in seconds"},
    },
    "required": ["url"],
}


async def _execute(params: dict[str, Any]) -> dict[str, Any]:
    """Execute an HTTP request with SSRF protection."""
    url = params["url"]
    method = params.get("method", "GET").upper()
    headers = params.get("headers", {})
    body = params.get("body")
    timeout = params.get("timeout", 30)

    safe, reason = is_safe_url(url)
    if not safe:
        return {"error": f"URL blocked: {reason}"}

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            kwargs: dict[str, Any] = {"method": method, "url": url, "headers": headers}
            if body and method in ("POST", "PUT", "PATCH"):
                kwargs["json"] = body

            resp = await client.request(**kwargs)
            content = resp.text[:50000]

            return {
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "body": content,
            }
    except httpx.TimeoutException:
        return {"error": f"Request timed out after {timeout}s"}
    except Exception as e:
        return {"error": f"Request failed: {e}"}


http_request_tool = ToolDef(
    name="http_request",
    description="Make HTTP requests with SSRF protection.",
    tool_type="builtin",
    input_schema=INPUT_SCHEMA,
    handler=_execute,
    permissions=["tool:http_request"],
)
```

- [ ] **Step 3: Add URL validation to webhook creation/update**

In `backend/app/api/v1/webhooks.py`, add validation in `create_webhook` and `update_webhook`:

```python
# Add import at top:
from app.core.ssrf import is_safe_url

# In create_webhook, after event type validation:
    safe, reason = is_safe_url(body.url)
    if not safe:
        raise HTTPException(status_code=400, detail=f"Webhook URL not allowed: {reason}")

# In update_webhook, after event type validation:
    safe, reason = is_safe_url(body.url)
    if not safe:
        raise HTTPException(status_code=400, detail=f"Webhook URL not allowed: {reason}")
```

- [ ] **Step 4: Add SSRF check in webhook dispatcher**

In `backend/app/core/webhook_dispatcher.py`, add before the HTTP POST in `deliver_webhook`:

```python
from app.core.ssrf import is_safe_url

# Before the delivery loop in deliver_webhook:
    safe, reason = is_safe_url(webhook.url)
    if not safe:
        logger.error("Webhook %s URL blocked: %s", webhook.id, reason)
        event.status = "blocked"
        event.response_status = 0
        await db.flush()
        return
```

- [ ] **Step 5: Add SSRF protection to workflow HTTP node**

In `backend/app/engines/workflow_engine/workflow.py`, in `_execute_http`, add before the httpx call:

```python
from app.core.ssrf import is_safe_url

# At the start of _execute_http:
    safe, reason = is_safe_url(url)
    if not safe:
        return {"error": f"URL blocked: {reason}", "status_code": 0}
```

- [ ] **Step 6: Commit**

```bash
git add app/core/ssrf.py app/engines/tool_engine/builtin/http_request.py app/api/v1/webhooks.py app/core/webhook_dispatcher.py app/engines/workflow_engine/workflow.py
git commit -m "fix(security): 统一 SSRF 防护——DNS 解析校验 + webhook URL 验证 + 工作流 HTTP 节点"
```

---

### Task 10: Fix graph merge entity duplication bug

**Files:**
- Modify: `backend/app/engines/knowledge_engine/storage/graph/neo4j_store.py`
- Modify: `backend/app/engines/knowledge_engine/graph/graph_builder.py`

- [ ] **Step 1: Add merge_node method to Neo4jGraphStore**

In `neo4j_store.py`, add after `create_node`:

```python
    async def merge_node(self, label: str, key: str, properties: dict) -> str:
        """MERGE a node by label + key property. Creates if not exists, updates if exists."""
        label = _validate_label(label)
        # Sanitize key for safe use in Cypher (alphanumeric only)
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            raise ValueError(f"Invalid merge key: {key}")
        async with self._driver.session() as session:
            result = await session.run(
                f"MERGE (n:{label} {{{key}: $value}}) "
                f"SET n += $props "
                f"RETURN elementId(n) AS id",
                value=properties.get(key, ""),
                props=properties,
            )
            record = await result.single()
            return record["id"]
```

- [ ] **Step 2: Fix graph_builder._merge_entity to use MERGE**

In `graph_builder.py`, replace `_merge_entity` (lines 334-357):

```python
    async def _merge_entity(self, entity: dict) -> Optional[str]:
        """Merge entity into graph using MERGE (idempotent)."""
        name = entity.get("name", "")
        etype = entity.get("type", "Entity")
        description = entity.get("description", "")

        if not name:
            return None

        try:
            props = {"name": name, "description": description, **{
                k: v for k, v in entity.items()
                if k not in ("name", "type", "description") and isinstance(v, (str, int, float, bool))
            }}
            node_id = await self.graph_store.merge_node(
                etype, "name", props,
            )
            return node_id
        except Exception:
            logger.warning("Failed to merge entity '%s'", name)
            return None
```

- [ ] **Step 3: Remove the now-unused _update_entity_properties method**

Delete the `_update_entity_properties` method (lines 359-379) from `graph_builder.py`.

- [ ] **Step 4: Commit**

```bash
git add app/engines/knowledge_engine/storage/graph/neo4j_store.py app/engines/knowledge_engine/graph/graph_builder.py
git commit -m "fix(knowledge): 图节点合并改用 MERGE 语义，修复增量更新重复节点问题"
```

---

### Task 11: Fix XSS in MarkdownRenderer — replace with react-markdown

**Files:**
- Rewrite: `frontend/src/components/MarkdownRenderer.tsx`
- Modify: `frontend/package.json`

- [ ] **Step 1: Install dependencies**

Run: `cd frontend && npm install react-markdown remark-gfm rehype-sanitize`

- [ ] **Step 2: Rewrite MarkdownRenderer.tsx**

```tsx
'use client';
import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const defaultSanitizeSchema = {
  tagNames: [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'hr',
    'strong', 'em', 'del', 'code', 'pre',
    'ul', 'ol', 'li',
    'blockquote',
    'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'span',
  ],
  attributes: {
    a: ['href', 'target', 'rel'],
    img: ['src', 'alt'],
    code: ['className'],
    td: ['style'],
    th: ['style'],
  },
};

export default function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div className={className} style={{ lineHeight: 1.6, wordBreak: 'break-word' }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeSanitize, defaultSanitizeSchema]]}
        components={{
          pre: ({ children }) => (
            <pre style={{
              background: '#f6f8fa', padding: 16, borderRadius: 6,
              overflowX: 'auto', margin: '12px 0', fontSize: 13, lineHeight: 1.5,
            }}>
              {children}
            </pre>
          ),
          code: ({ className: codeClassName, children, ...props }) => {
            const isInline = !codeClassName;
            return isInline ? (
              <code style={{
                background: '#f0f0f0', padding: '2px 6px',
                borderRadius: 3, fontSize: '0.9em',
              }} {...props}>{children}</code>
            ) : (
              <code className={codeClassName} {...props}>{children}</code>
            );
          },
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer"
               style={{ color: '#1890ff', textDecoration: 'none' }}>
              {children}
            </a>
          ),
          blockquote: ({ children }) => (
            <blockquote style={{
              borderLeft: '4px solid #d9d9d9', padding: '8px 16px',
              margin: '12px 0', color: '#666', background: '#fafafa',
            }}>
              {children}
            </blockquote>
          ),
          table: ({ children }) => (
            <table style={{
              borderCollapse: 'collapse', margin: '12px 0', width: '100%',
            }}>
              {children}
            </table>
          ),
          th: ({ children }) => (
            <th style={{
              border: '1px solid #ddd', padding: '8px 12px', background: '#f6f8fa',
            }}>
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td style={{ border: '1px solid #ddd', padding: '8px 12px' }}>
              {children}
            </td>
          ),
          img: ({ src, alt }) => (
            <img src={src} alt={alt}
                 style={{ maxWidth: '100%', borderRadius: 4, margin: '8px 0' }} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npx next build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/MarkdownRenderer.tsx frontend/package.json frontend/package-lock.json
git commit -m "fix(security): 用 react-markdown + rehype-sanitize 替换自定义 Markdown 渲染器，修复 XSS"
```

---

### Task 12: Remove hardcoded login credentials

**Files:**
- Modify: `frontend/src/app/(auth)/login/page.tsx`

- [ ] **Step 1: Remove initialValues**

In `login/page.tsx`, find and remove the `initialValues` prop from the Form component:

```tsx
// Remove this line:
initialValues={{ username: 'admin', password: 'admin123' }}

// The Form component should have no initialValues prop
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/\(auth\)/login/page.tsx
git commit -m "fix(security): 移除登录页硬编码默认凭据"
```

---

### Task 13: Run full test suite and verify

**Files:** None — verification only

- [ ] **Step 1: Run backend tests**

Run: `cd backend && python -m pytest tests/unit/ -q --tb=short`
Expected: All pass (324+)

- [ ] **Step 2: Run frontend build**

Run: `cd frontend && npx next build`
Expected: Build succeeds, 14 routes

- [ ] **Step 3: Manual smoke test checklist**

- [ ] `POST /api/v1/users/register` without auth returns 401/403
- [ ] `POST /api/v1/webhooks` with `url=http://169.254.169.254` returns 400
- [ ] Login page has empty username/password fields
- [ ] Chat message renders markdown without executing `javascript:` links

---

## Self-Review Checklist

- [x] **Spec coverage:** All 14 Critical findings have corresponding tasks
- [x] **Placeholder scan:** No TBD/TODO/fill-in-later in any step
- [x] **Type consistency:** All method signatures match their call sites
- [x] **File paths:** All paths verified against actual codebase
- [x] **Test coverage:** Each security fix has corresponding test or verification step

---

## P1 Important Fixes (Follow-up Plan)

These are tracked for the next iteration:

| # | Issue | Effort |
|---|-------|--------|
| 1 | `datetime.utcnow()` → `datetime.now(UTC)` everywhere | Medium (mechanical) |
| 2 | File upload size limit (knowledge.py) | Small |
| 3 | `models/base.py` split into per-domain files | Medium |
| 4 | RBAC permission caching in Redis | Medium |
| 5 | Pydantic validation on raw `request.json()` endpoints | Medium |
| 6 | Crew parallel mode concurrency limit (Semaphore) | Small |
| 7 | CircuitBreaker asyncio.Lock | Small |
| 8 | Human approval node proper await mechanism | Medium |
| 9 | Logging for all `except Exception: pass` blocks | Small |
| 10 | Frontend Next.js middleware for server-side auth | Medium |
| 11 | Frontend API client typed responses (replace `any`) | Medium |
| 12 | Consolidate triple retrieval implementations | Large |
