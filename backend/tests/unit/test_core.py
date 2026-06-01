import pytest

from app.core.exceptions import AgentEngineError, ModelNotFoundError
from app.core.security import (
    create_access_token,
    decode_token,
    decrypt,
    encrypt,
    get_password_hash,
    verify_password,
)
from app.schemas.common import LLMResponse, TokenUsage


def test_agent_engine_error_hierarchy():
    assert issubclass(ModelNotFoundError, AgentEngineError)
    assert issubclass(ModelNotFoundError, Exception)


def test_password_hash():
    hashed = get_password_hash("test123")
    assert verify_password("test123", hashed)
    assert not verify_password("wrong", hashed)


def test_token_creation():
    token = create_access_token({"sub": "user1"})
    payload = decode_token(token)
    assert payload["sub"] == "user1"
    assert "exp" in payload


def test_token_usage():
    usage = TokenUsage(input_tokens=100, output_tokens=50)
    assert usage.total_tokens == 0  # default, not auto-calculated


def test_llm_response():
    resp = LLMResponse(content="hello", model="gpt-4", usage=TokenUsage())
    assert resp.content == "hello"
    assert resp.finish_reason == "stop"


def test_encrypt_decrypt():
    original = "sensitive-api-key-12345"
    encrypted = encrypt(original)
    assert encrypted != original
    assert decrypt(encrypted) == original
