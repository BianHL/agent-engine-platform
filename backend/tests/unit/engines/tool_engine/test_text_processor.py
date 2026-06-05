"""Unit tests for text_processor builtin tools: 7 handlers."""
from __future__ import annotations

import base64
import json
import re
from datetime import datetime, UTC

import pytest

from app.engines.tool_engine.builtin.text_processor import (
    _text_summarize_handler,
    _json_process_handler,
    _hash_handler,
    _base64_handler,
    _uuid_handler,
    _regex_handler,
    _datetime_handler,
    text_summarizer_tool,
    json_processor_tool,
    hash_generator_tool,
    base64_codec_tool,
    uuid_generator_tool,
    regex_engine_tool,
    date_time_tool,
)


# ---------------------------------------------------------------------------
# text_summarizer
# ---------------------------------------------------------------------------


class TestTextSummarizer:
    @pytest.mark.asyncio
    async def test_truncate_short_text(self):
        result = await _text_summarize_handler({"text": "Hello world"})
        assert result["summary"] == "Hello world"
        assert result["compression_ratio"] == 1.0

    @pytest.mark.asyncio
    async def test_truncate_long_text(self):
        text = "A" * 500
        result = await _text_summarize_handler({"text": text, "max_length": 100})
        assert len(result["summary"]) <= 105  # "..." appended
        assert result["original_length"] == 500

    @pytest.mark.asyncio
    async def test_truncate_breaks_at_sentence(self):
        text = "First sentence. Second sentence. Third sentence that is very long and goes on and on and on and on and on and on and on and on and on and on and on and on and on."
        result = await _text_summarize_handler({"text": text, "max_length": 80})
        assert result["summary"].endswith(".")

    @pytest.mark.asyncio
    async def test_first_sentence_strategy(self):
        text = "Hello world. This is second. Third."
        result = await _text_summarize_handler({"text": text, "strategy": "first_sentence"})
        assert "Hello world" in result["summary"]

    @pytest.mark.asyncio
    async def test_empty_text(self):
        result = await _text_summarize_handler({"text": ""})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_tool_definition(self):
        assert text_summarizer_tool.name == "text_summarizer"
        assert "text" in text_summarizer_tool.input_schema["required"]


# ---------------------------------------------------------------------------
# json_processor
# ---------------------------------------------------------------------------


class TestJsonProcessor:
    @pytest.mark.asyncio
    async def test_validate_valid_json(self):
        result = await _json_process_handler({"data": '{"a": 1}', "operation": "validate"})
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_invalid_json(self):
        result = await _json_process_handler({"data": "not json", "operation": "validate"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_format_json(self):
        result = await _json_process_handler({"data": '{"a":1}', "operation": "format"})
        assert "\n" in result["formatted"]

    @pytest.mark.asyncio
    async def test_extract_nested_path(self):
        data = json.dumps({"user": {"name": "Alice", "address": {"city": "Beijing"}}})
        result = await _json_process_handler({"data": data, "operation": "extract", "path": "user.address.city"})
        assert result["value"] == "Beijing"

    @pytest.mark.asyncio
    async def test_extract_array_index(self):
        data = json.dumps({"items": [10, 20, 30]})
        result = await _json_process_handler({"data": data, "operation": "extract", "path": "items.1"})
        assert result["value"] == 20

    @pytest.mark.asyncio
    async def test_extract_missing_path(self):
        result = await _json_process_handler({"data": '{"a":1}', "operation": "extract", "path": "b.c"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_merge_objects(self):
        data = [json.dumps({"a": 1}), json.dumps({"b": 2})]
        result = await _json_process_handler({"data": data, "operation": "merge"})
        assert result["merged"] == {"a": 1, "b": 2}

    @pytest.mark.asyncio
    async def test_merge_non_array_error(self):
        result = await _json_process_handler({"data": '{"a":1}', "operation": "merge"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_unknown_operation(self):
        result = await _json_process_handler({"data": "{}", "operation": "explode"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_tool_definition(self):
        assert json_processor_tool.name == "json_processor"


# ---------------------------------------------------------------------------
# hash_generator
# ---------------------------------------------------------------------------


class TestHashGenerator:
    @pytest.mark.asyncio
    async def test_sha256_default(self):
        result = await _hash_handler({"data": "hello"})
        assert result["algorithm"] == "sha256"
        assert len(result["hash"]) == 64

    @pytest.mark.asyncio
    async def test_md5(self):
        result = await _hash_handler({"data": "hello", "algorithm": "md5"})
        assert result["algorithm"] == "md5"
        assert len(result["hash"]) == 32

    @pytest.mark.asyncio
    async def test_sha1(self):
        result = await _hash_handler({"data": "hello", "algorithm": "sha1"})
        assert len(result["hash"]) == 40

    @pytest.mark.asyncio
    async def test_sha512(self):
        result = await _hash_handler({"data": "hello", "algorithm": "sha512"})
        assert len(result["hash"]) == 128

    @pytest.mark.asyncio
    async def test_empty_data(self):
        result = await _hash_handler({"data": ""})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_unsupported_algorithm(self):
        result = await _hash_handler({"data": "hello", "algorithm": "blake2b"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_consistency(self):
        r1 = await _hash_handler({"data": "test"})
        r2 = await _hash_handler({"data": "test"})
        assert r1["hash"] == r2["hash"]

    @pytest.mark.asyncio
    async def test_tool_definition(self):
        assert hash_generator_tool.name == "hash_generator"


# ---------------------------------------------------------------------------
# base64_codec
# ---------------------------------------------------------------------------


class TestBase64Codec:
    @pytest.mark.asyncio
    async def test_encode(self):
        result = await _base64_handler({"data": "hello", "operation": "encode"})
        assert base64.b64decode(result["result"]).decode() == "hello"

    @pytest.mark.asyncio
    async def test_decode(self):
        encoded = base64.b64encode(b"hello").decode()
        result = await _base64_handler({"data": encoded, "operation": "decode"})
        assert result["result"] == "hello"

    @pytest.mark.asyncio
    async def test_roundtrip(self):
        enc = await _base64_handler({"data": "中文测试", "operation": "encode"})
        dec = await _base64_handler({"data": enc["result"], "operation": "decode"})
        assert dec["result"] == "中文测试"

    @pytest.mark.asyncio
    async def test_empty_data(self):
        result = await _base64_handler({"data": ""})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_unknown_operation(self):
        result = await _base64_handler({"data": "x", "operation": "encrypt"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_tool_definition(self):
        assert base64_codec_tool.name == "base64_codec"


# ---------------------------------------------------------------------------
# uuid_generator
# ---------------------------------------------------------------------------


class TestUuidGenerator:
    @pytest.mark.asyncio
    async def test_single_uuid_v4(self):
        result = await _uuid_handler({})
        assert result["count"] == 1
        assert result["version"] == 4
        assert len(result["uuids"][0]) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_multiple_uuids(self):
        result = await _uuid_handler({"count": 5})
        assert result["count"] == 5
        assert len(set(result["uuids"])) == 5  # all unique

    @pytest.mark.asyncio
    async def test_count_capped_at_100(self):
        result = await _uuid_handler({"count": 999})
        assert result["count"] == 100

    @pytest.mark.asyncio
    async def test_count_minimum_1(self):
        result = await _uuid_handler({"count": 0})
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_uuid_v1(self):
        result = await _uuid_handler({"version": 1})
        assert result["version"] == 1

    @pytest.mark.asyncio
    async def test_uuid_v5(self):
        result = await _uuid_handler({
            "version": 5,
            "namespace": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "name": "example.com",
        })
        assert result["version"] == 5
        assert len(result["uuids"]) == 1

    @pytest.mark.asyncio
    async def test_tool_definition(self):
        assert uuid_generator_tool.name == "uuid_generator"


# ---------------------------------------------------------------------------
# regex_engine
# ---------------------------------------------------------------------------


class TestRegexEngine:
    @pytest.mark.asyncio
    async def test_find(self):
        result = await _regex_handler({"text": "abc 123 def 456", "pattern": r"\d+", "operation": "find"})
        assert result["matches"] == ["123", "456"]
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_match(self):
        result = await _regex_handler({"text": "hello world", "pattern": r"world", "operation": "match"})
        assert result["matched"] is True
        assert result["match"] == "world"

    @pytest.mark.asyncio
    async def test_match_no_hit(self):
        result = await _regex_handler({"text": "hello", "pattern": r"xyz", "operation": "match"})
        assert result["matched"] is False

    @pytest.mark.asyncio
    async def test_replace(self):
        result = await _regex_handler({
            "text": "foo bar foo", "pattern": "foo", "operation": "replace", "replacement": "baz",
        })
        assert result["result"] == "baz bar baz"

    @pytest.mark.asyncio
    async def test_split(self):
        result = await _regex_handler({"text": "a,b,,c", "pattern": ",", "operation": "split"})
        assert result["parts"] == ["a", "b", "", "c"]

    @pytest.mark.asyncio
    async def test_empty_text(self):
        result = await _regex_handler({"text": "", "pattern": r"\d+"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_regex(self):
        result = await _regex_handler({"text": "hello", "pattern": "[invalid"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_unknown_operation(self):
        result = await _regex_handler({"text": "a", "pattern": "a", "operation": "explode"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_tool_definition(self):
        assert regex_engine_tool.name == "regex_engine"


# ---------------------------------------------------------------------------
# date_time
# ---------------------------------------------------------------------------


class TestDateTime:
    @pytest.mark.asyncio
    async def test_now(self):
        result = await _datetime_handler({"operation": "now"})
        assert "datetime" in result
        assert "timestamp" in result
        assert "iso" in result

    @pytest.mark.asyncio
    async def test_parse(self):
        result = await _datetime_handler({"operation": "parse", "date": "2024-01-15T10:30:00"})
        assert result["year"] == 2024
        assert result["month"] == 1
        assert result["day"] == 15

    @pytest.mark.asyncio
    async def test_format(self):
        result = await _datetime_handler({
            "operation": "format", "date": "2024-01-15T10:30:00", "format": "%d/%m/%Y",
        })
        assert result["formatted"] == "15/01/2024"

    @pytest.mark.asyncio
    async def test_diff(self):
        result = await _datetime_handler({
            "operation": "diff",
            "date1": "2024-01-01T00:00:00",
            "date2": "2024-01-03T00:00:00",
        })
        assert result["days"] == 2

    @pytest.mark.asyncio
    async def test_parse_missing_date(self):
        result = await _datetime_handler({"operation": "parse"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_diff_missing_dates(self):
        result = await _datetime_handler({"operation": "diff", "date1": "2024-01-01"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_unknown_operation(self):
        result = await _datetime_handler({"operation": "explode"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_tool_definition(self):
        assert date_time_tool.name == "date_time"
