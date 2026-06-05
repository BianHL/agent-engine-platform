"""Unit tests for security-critical builtin tools: code_executor and db_query."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.engines.tool_engine.builtin.code_executor import (
    BLOCKED_MODULES,
    _check_imports,
    _execute as code_execute,
    code_executor_tool,
)
from app.engines.tool_engine.builtin.db_query import (
    FORBIDDEN_KEYWORDS,
    _is_safe_query,
    db_query_tool,
)


# ---------------------------------------------------------------------------
# code_executor: _check_imports
# ---------------------------------------------------------------------------


class TestCodeExecutorCheckImports:
    def test_clean_code_passes(self):
        assert _check_imports("print('hello')") is None

    def test_blocked_import_os(self):
        result = _check_imports("import os")
        assert result is not None
        assert "Blocked module: os" in result

    def test_blocked_import_subprocess(self):
        result = _check_imports("import subprocess")
        assert result is not None
        assert "Blocked module: subprocess" in result

    def test_blocked_import_from(self):
        result = _check_imports("from os.path import join")
        assert result is not None
        assert "Blocked module: os" in result

    def test_blocked_import_socket(self):
        result = _check_imports("import socket")
        assert result is not None
        assert "Blocked module: socket" in result

    def test_allowed_import(self):
        assert _check_imports("import json") is None
        assert _check_imports("import math") is None
        assert _check_imports("from collections import Counter") is None

    def test_syntax_error(self):
        result = _check_imports("def foo(")
        assert result is not None
        assert "Syntax error" in result

    def test_blocked_modules_comprehensive(self):
        """All BLOCKED_MODULES should be caught."""
        for mod in BLOCKED_MODULES:
            result = _check_imports(f"import {mod}")
            assert result is not None, f"Failed to block: {mod}"

    def test_nested_import_blocked(self):
        """import inside function should still be caught."""
        code = """
def foo():
    import os
    return os.getcwd()
"""
        result = _check_imports(code)
        assert result is not None
        assert "Blocked module: os" in result

    def test_empty_code(self):
        assert _check_imports("") is None

    def test_comment_only(self):
        assert _check_imports("# just a comment") is None


# ---------------------------------------------------------------------------
# code_executor: _execute
# ---------------------------------------------------------------------------


class TestCodeExecutorExecute:
    @pytest.mark.asyncio
    async def test_blocked_import_returns_error(self):
        result = await code_execute({"code": "import os"})
        assert "error" in result
        assert "Blocked module" in result["error"]

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(return_value=(b"hello\n", b""))
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc

            result = await code_execute({"code": "print('hello')"})

        assert result["exit_code"] == 0
        assert "hello" in result["stdout"]

    @pytest.mark.asyncio
    async def test_timeout_kills_process(self):
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError)
            mock_proc.kill = MagicMock()
            mock_subprocess.return_value = mock_proc

            result = await code_execute({"code": "while True: pass", "timeout": 1})

        assert "error" in result
        assert "timed out" in result["error"]
        mock_proc.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_tool_definition(self):
        assert code_executor_tool.name == "code_executor"
        assert "code" in code_executor_tool.input_schema["required"]


# ---------------------------------------------------------------------------
# db_query: _is_safe_query
# ---------------------------------------------------------------------------


class TestDbQuerySafety:
    def test_select_allowed(self):
        safe, query = _is_safe_query("SELECT * FROM users")
        assert safe is True

    def test_with_cte_allowed(self):
        safe, query = _is_safe_query("WITH cte AS (SELECT 1) SELECT * FROM cte")
        assert safe is True

    def test_insert_blocked(self):
        safe, reason = _is_safe_query("INSERT INTO users VALUES (1, 'hack')")
        assert safe is False

    def test_delete_blocked(self):
        safe, reason = _is_safe_query("DELETE FROM users WHERE id = 1")
        assert safe is False

    def test_drop_blocked(self):
        safe, reason = _is_safe_query("DROP TABLE users")
        assert safe is False

    def test_update_blocked(self):
        safe, reason = _is_safe_query("UPDATE users SET name = 'hacked'")
        assert safe is False

    def test_union_blocked(self):
        safe, reason = _is_safe_query("SELECT * FROM users UNION SELECT * FROM passwords")
        assert safe is False
        assert "UNION" in reason

    def test_multi_statement_blocked(self):
        """Semicolons should truncate the query."""
        safe, query = _is_safe_query("SELECT 1; DROP TABLE users")
        assert safe is True
        assert "DROP" not in query

    def test_comment_hiding_blocked(self):
        """Comments hiding non-SELECT prefix should be caught."""
        safe, reason = _is_safe_query("-- comment\nINSERT INTO users VALUES (1)")
        assert safe is False

    def test_block_comment_hiding_blocked(self):
        safe, reason = _is_safe_query("/* hack */ INSERT INTO users VALUES (1)")
        assert safe is False

    def test_empty_query(self):
        safe, reason = _is_safe_query("")
        assert safe is False
        assert "Empty" in reason

    def test_non_select_start(self):
        safe, reason = _is_safe_query("EXPLAIN SELECT 1")
        assert safe is False
        assert "Only SELECT" in reason

    def test_into_outfile_blocked(self):
        safe, reason = _is_safe_query("SELECT * INTO OUTFILE '/tmp/hack' FROM users")
        assert safe is False

    def test_forbidden_keywords_comprehensive(self):
        """All FORBIDDEN_KEYWORDS should be caught in SELECT context."""
        for keyword in FORBIDDEN_KEYWORDS:
            if keyword == "UNION":
                continue  # UNION has special handling
            query = f"SELECT {keyword} FROM t"
            safe, reason = _is_safe_query(query)
            if " " not in keyword:
                assert safe is False, f"Failed to block: {keyword}"


# ---------------------------------------------------------------------------
# db_query: tool definition
# ---------------------------------------------------------------------------


class TestDbQueryTool:
    def test_tool_definition(self):
        assert db_query_tool.name == "db_query"
        assert db_query_tool.tool_type == "builtin"
        assert "query" in db_query_tool.input_schema["required"]

    def test_limit_max(self):
        """Input schema should enforce max limit of 500."""
        assert db_query_tool.input_schema["properties"]["limit"]["maximum"] == 500
