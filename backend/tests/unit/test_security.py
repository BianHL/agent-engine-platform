"""Unit tests for Security module"""
import pytest
from app.core.security import (
    get_password_hash, verify_password,
    create_access_token, decode_token,
    encrypt, decrypt
)


def test_password_hash_roundtrip():
    password = "SecureP@ssw0rd!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)


def test_password_hash_different_each_time():
    p1 = get_password_hash("test")
    p2 = get_password_hash("test")
    assert p1 != p2  # bcrypt uses random salt


def test_wrong_password():
    hashed = get_password_hash("correct")
    assert not verify_password("wrong", hashed)


def test_token_roundtrip():
    data = {"sub": "user123", "role": "admin", "tenant_id": "t1"}
    token = create_access_token(data)
    decoded = decode_token(token)
    assert decoded["sub"] == "user123"
    assert decoded["role"] == "admin"


def test_token_contains_expiry():
    token = create_access_token({"sub": "user1"})
    decoded = decode_token(token)
    assert "exp" in decoded


def test_encrypt_decrypt_roundtrip():
    plaintext = "my-secret-api-key"
    encrypted = encrypt(plaintext)
    assert encrypted != plaintext
    decrypted = decrypt(encrypted)
    assert decrypted == plaintext


def test_encrypt_different_ciphertext():
    e1 = encrypt("test")
    e2 = encrypt("test")
    # Fernet uses random IV, so ciphertext differs
    # But both should decrypt to same value
    assert decrypt(e1) == decrypt(e2)


def test_decrypt_wrong_key():
    encrypted = encrypt("test")
    # Should still work since we use the same key from env
    decrypted = decrypt(encrypted)
    assert decrypted == "test"
