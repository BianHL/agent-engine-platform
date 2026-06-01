"""Built-in text processing tools."""
from __future__ import annotations

import hashlib
import re
import uuid
import base64
import json
from datetime import datetime, UTC
from typing import Any

from app.engines.tool_engine.registry import ToolDef


async def _text_summarize_handler(params: dict[str, Any]) -> dict[str, Any]:
    """Summarize text (simple truncation-based, can be enhanced with LLM)."""
    text = params.get("text", "")
    max_length = params.get("max_length", 200)
    strategy = params.get("strategy", "truncate")

    if not text:
        return {"error": "No text provided"}

    if strategy == "truncate":
        if len(text) <= max_length:
            summary = text
        else:
            # Try to break at sentence boundary
            truncated = text[:max_length]
            last_period = truncated.rfind(".")
            last_question = truncated.rfind("?")
            last_exclaim = truncated.rfind("!")
            break_point = max(last_period, last_question, last_exclaim)
            summary = truncated[:break_point + 1] if break_point > max_length * 0.5 else truncated + "..."
    elif strategy == "first_sentence":
        sentences = re.split(r'[.!?]+', text)
        summary = sentences[0].strip() + "." if sentences else text[:max_length]
    else:
        summary = text[:max_length]

    return {
        "summary": summary,
        "original_length": len(text),
        "summary_length": len(summary),
        "compression_ratio": round(len(summary) / len(text), 2) if text else 0,
    }


async def _json_process_handler(params: dict[str, Any]) -> dict[str, Any]:
    """Process JSON data with various operations."""
    operation = params.get("operation", "validate")
    data = params.get("data", "")
    path = params.get("path", "")

    try:
        if operation == "validate":
            json.loads(data) if isinstance(data, str) else data
            return {"valid": True, "message": "Valid JSON"}

        elif operation == "format":
            parsed = json.loads(data) if isinstance(data, str) else data
            return {"formatted": json.dumps(parsed, indent=2, ensure_ascii=False)}

        elif operation == "extract":
            parsed = json.loads(data) if isinstance(data, str) else data
            if path:
                keys = path.split(".")
                result = parsed
                for key in keys:
                    if isinstance(result, dict) and key in result:
                        result = result[key]
                    elif isinstance(result, list) and key.isdigit():
                        result = result[int(key)]
                    else:
                        return {"error": f"Path not found: {path}"}
                return {"value": result}
            return {"value": parsed}

        elif operation == "merge":
            if isinstance(data, list):
                merged = {}
                for item in data:
                    parsed = json.loads(item) if isinstance(item, str) else item
                    merged.update(parsed)
                return {"merged": merged}
            return {"error": "Data must be array for merge operation"}

        else:
            return {"error": f"Unknown operation: {operation}"}

    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}


async def _hash_handler(params: dict[str, Any]) -> dict[str, Any]:
    """Generate hash of input data."""
    data = params.get("data", "")
    algorithm = params.get("algorithm", "sha256")

    if not data:
        return {"error": "No data provided"}

    data_bytes = data.encode("utf-8")

    algorithms = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
    }

    if algorithm not in algorithms:
        return {"error": f"Unsupported algorithm: {algorithm}. Use: {', '.join(algorithms.keys())}"}

    hash_obj = algorithms[algorithm](data_bytes)
    return {
        "hash": hash_obj.hexdigest(),
        "algorithm": algorithm,
        "input_length": len(data),
    }


async def _base64_handler(params: dict[str, Any]) -> dict[str, Any]:
    """Encode or decode base64 data."""
    data = params.get("data", "")
    operation = params.get("operation", "encode")

    if not data:
        return {"error": "No data provided"}

    try:
        if operation == "encode":
            encoded = base64.b64encode(data.encode("utf-8")).decode("utf-8")
            return {"result": encoded, "operation": "encode"}
        elif operation == "decode":
            decoded = base64.b64decode(data).decode("utf-8")
            return {"result": decoded, "operation": "decode"}
        else:
            return {"error": f"Unknown operation: {operation}. Use 'encode' or 'decode'"}
    except Exception as e:
        return {"error": f"Base64 operation failed: {str(e)}"}


async def _uuid_handler(params: dict[str, Any]) -> dict[str, Any]:
    """Generate UUID."""
    version = params.get("version", 4)
    count = params.get("count", 1)
    namespace = params.get("namespace", "")
    name = params.get("name", "")

    count = min(max(count, 1), 100)  # Limit to 100

    uuids = []
    for _ in range(count):
        if version == 1:
            u = uuid.uuid1()
        elif version == 4:
            u = uuid.uuid4()
        elif version == 5 and namespace and name:
            ns_uuid = uuid.UUID(namespace) if namespace else uuid.NAMESPACE_DNS
            u = uuid.uuid5(ns_uuid, name)
        else:
            u = uuid.uuid4()
        uuids.append(str(u))

    return {
        "uuids": uuids,
        "count": len(uuids),
        "version": version,
    }


async def _regex_handler(params: dict[str, Any]) -> dict[str, Any]:
    """Apply regex operations to text."""
    text = params.get("text", "")
    pattern = params.get("pattern", "")
    operation = params.get("operation", "find")
    replacement = params.get("replacement", "")

    if not text or not pattern:
        return {"error": "Both text and pattern are required"}

    try:
        if operation == "find":
            matches = re.findall(pattern, text)
            return {"matches": matches, "count": len(matches)}

        elif operation == "match":
            match = re.search(pattern, text)
            if match:
                return {
                    "matched": True,
                    "match": match.group(),
                    "groups": list(match.groups()),
                    "start": match.start(),
                    "end": match.end(),
                }
            return {"matched": False}

        elif operation == "replace":
            result = re.sub(pattern, replacement, text)
            return {"result": result, "replacements": text.count(pattern)}

        elif operation == "split":
            parts = re.split(pattern, text)
            return {"parts": parts, "count": len(parts)}

        else:
            return {"error": f"Unknown operation: {operation}"}

    except re.error as e:
        return {"error": f"Invalid regex: {str(e)}"}


async def _datetime_handler(params: dict[str, Any]) -> dict[str, Any]:
    """Date/time operations."""
    operation = params.get("operation", "now")
    format_str = params.get("format", "%Y-%m-%d %H:%M:%S")
    date_str = params.get("date", "")

    try:
        if operation == "now":
            now = datetime.now(UTC)
            return {
                "datetime": now.strftime(format_str),
                "timestamp": now.timestamp(),
                "iso": now.isoformat(),
            }

        elif operation == "parse":
            if not date_str:
                return {"error": "Date string required for parse operation"}
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return {
                "datetime": dt.strftime(format_str),
                "timestamp": dt.timestamp(),
                "iso": dt.isoformat(),
                "year": dt.year,
                "month": dt.month,
                "day": dt.day,
                "hour": dt.hour,
                "minute": dt.minute,
                "second": dt.second,
            }

        elif operation == "format":
            if not date_str:
                return {"error": "Date string required for format operation"}
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return {"formatted": dt.strftime(format_str)}

        elif operation == "diff":
            date1 = params.get("date1", "")
            date2 = params.get("date2", "")
            if not date1 or not date2:
                return {"error": "Both date1 and date2 required for diff operation"}
            dt1 = datetime.fromisoformat(date1.replace("Z", "+00:00"))
            dt2 = datetime.fromisoformat(date2.replace("Z", "+00:00"))
            diff = dt2 - dt1
            return {
                "days": diff.days,
                "seconds": diff.seconds,
                "total_seconds": diff.total_seconds(),
            }

        else:
            return {"error": f"Unknown operation: {operation}"}

    except Exception as e:
        return {"error": f"DateTime operation failed: {str(e)}"}


# Tool definitions

text_summarizer_tool = ToolDef(
    name="text_summarizer",
    description="Summarize text using various strategies (truncate, first_sentence)",
    tool_type="builtin",
    input_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to summarize"},
            "max_length": {"type": "integer", "description": "Maximum summary length", "default": 200},
            "strategy": {"type": "string", "enum": ["truncate", "first_sentence"], "default": "truncate"},
        },
        "required": ["text"],
    },
    handler=_text_summarize_handler,
)

json_processor_tool = ToolDef(
    name="json_processor",
    description="Process JSON data: validate, format, extract, merge",
    tool_type="builtin",
    input_schema={
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["validate", "format", "extract", "merge"], "default": "validate"},
            "data": {"description": "JSON data to process (string or object)"},
            "path": {"type": "string", "description": "Dot-separated path for extract operation"},
        },
        "required": ["data"],
    },
    handler=_json_process_handler,
)

hash_generator_tool = ToolDef(
    name="hash_generator",
    description="Generate hash of input data (MD5, SHA1, SHA256, SHA512)",
    tool_type="builtin",
    input_schema={
        "type": "object",
        "properties": {
            "data": {"type": "string", "description": "Data to hash"},
            "algorithm": {"type": "string", "enum": ["md5", "sha1", "sha256", "sha512"], "default": "sha256"},
        },
        "required": ["data"],
    },
    handler=_hash_handler,
)

base64_codec_tool = ToolDef(
    name="base64_codec",
    description="Encode or decode base64 data",
    tool_type="builtin",
    input_schema={
        "type": "object",
        "properties": {
            "data": {"type": "string", "description": "Data to encode/decode"},
            "operation": {"type": "string", "enum": ["encode", "decode"], "default": "encode"},
        },
        "required": ["data"],
    },
    handler=_base64_handler,
)

uuid_generator_tool = ToolDef(
    name="uuid_generator",
    description="Generate UUIDs (v1, v4, v5)",
    tool_type="builtin",
    input_schema={
        "type": "object",
        "properties": {
            "version": {"type": "integer", "enum": [1, 4, 5], "default": 4},
            "count": {"type": "integer", "description": "Number of UUIDs to generate", "default": 1, "minimum": 1, "maximum": 100},
            "namespace": {"type": "string", "description": "Namespace UUID for v5"},
            "name": {"type": "string", "description": "Name for v5 UUID"},
        },
    },
    handler=_uuid_handler,
)

regex_engine_tool = ToolDef(
    name="regex_engine",
    description="Apply regex operations: find, match, replace, split",
    tool_type="builtin",
    input_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to process"},
            "pattern": {"type": "string", "description": "Regex pattern"},
            "operation": {"type": "string", "enum": ["find", "match", "replace", "split"], "default": "find"},
            "replacement": {"type": "string", "description": "Replacement string for replace operation"},
        },
        "required": ["text", "pattern"],
    },
    handler=_regex_handler,
)

date_time_tool = ToolDef(
    name="date_time",
    description="Date/time operations: now, parse, format, diff",
    tool_type="builtin",
    input_schema={
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["now", "parse", "format", "diff"], "default": "now"},
            "format": {"type": "string", "description": "DateTime format string", "default": "%Y-%m-%d %H:%M:%S"},
            "date": {"type": "string", "description": "Date string to parse/format"},
            "date1": {"type": "string", "description": "First date for diff"},
            "date2": {"type": "string", "description": "Second date for diff"},
        },
    },
    handler=_datetime_handler,
)
