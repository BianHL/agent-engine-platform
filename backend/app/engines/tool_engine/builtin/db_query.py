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
    "LOAD DATA", "UNION",
}

_ALLOWED_STARTS = ("SELECT", "WITH")


def _is_safe_query(query: str) -> tuple[bool, str]:
    """Validate query is read-only. Returns (safe, cleaned_query_or_reason)."""
    # Strip SQL comments (-- line comments and /* block comments */)
    cleaned = re.sub(r"--[^\n]*", "", query, flags=re.MULTILINE)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()

    # Remove everything after semicolons (prevent multi-statement)
    if ";" in cleaned:
        cleaned = cleaned[:cleaned.index(";")].strip()

    if not cleaned:
        return False, "Empty query"

    upper = cleaned.upper()

    # Must start with SELECT (WITH is allowed as it wraps SELECT)
    if not upper.startswith(_ALLOWED_STARTS):
        return False, "Only SELECT or WITH queries are allowed"

    # After stripping comments, re-validate the cleaned query also starts correctly
    # (catches cases where comments hide a non-SELECT prefix)
    stripped_prefix = cleaned.lstrip()
    if not stripped_prefix.upper().startswith(_ALLOWED_STARTS):
        return False, "Only SELECT or WITH queries are allowed"

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper, flags=re.IGNORECASE):
            return False, f"Forbidden keyword: {keyword}"

    return True, cleaned


async def _execute(params: dict[str, Any]) -> dict[str, Any]:
    """Execute a read-only SQL query."""
    query = params["query"]
    limit = min(params.get("limit", 100), 500)

    safe, result = _is_safe_query(query)
    if not safe:
        return {"error": result}

    cleaned_query = result

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
