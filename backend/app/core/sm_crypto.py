"""国密算法工具类 (SM2/SM3/SM4).

This module provides wrappers for Chinese national cryptographic algorithms.
Install gmssl: pip install gmssl

Usage:
    Set CRYPTO_BACKEND=gm in config to enable national crypto.
    Falls back to standard crypto when gmssl is not installed.
"""
from __future__ import annotations

import hashlib
import logging
import os

logger = logging.getLogger(__name__)

# Try to import gmssl, gracefully degrade if not available
try:
    from gmssl import sm4 as _sm4
    from gmssl.sm3 import sm3_hash as _sm3_hash
    HAS_GMSSL = True
except ImportError:
    HAS_GMSSL = False
    logger.warning("gmssl not installed, national crypto features disabled")


class SM3Helper:
    """SM3哈希算法 (256-bit output)."""

    @staticmethod
    def hash(data: str | bytes) -> str:
        """Compute SM3 hash."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        if HAS_GMSSL:
            return _sm3_hash(data)
        # Fallback: use sha256 (not SM3, but maintains interface)
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def hash_password(password: str, salt: str = "") -> str:
        """Hash a password with optional salt using SM3."""
        if not salt:
            salt = os.urandom(16).hex()
        combined = f"{salt}:{password}"
        hashed = SM3Helper.hash(combined)
        return f"{salt}${hashed}"

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verify a password against a stored SM3 hash."""
        if "$" not in stored_hash:
            return False
        salt, expected = stored_hash.split("$", 1)
        combined = f"{salt}:{password}"
        actual = SM3Helper.hash(combined)
        return actual == expected


class SM4Helper:
    """SM4对称加密 (128-bit key, ECB mode)."""

    def __init__(self, key: bytes):
        if len(key) != 16:
            raise ValueError("SM4 key must be 16 bytes")
        self._key = key

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data with SM4."""
        if not HAS_GMSSL:
            # Fallback: use AES
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            cipher = Cipher(algorithms.AES(self._key), modes.ECB())
            encryptor = cipher.encryptor()
            # PKCS7 padding
            pad_len = 16 - (len(data) % 16)
            padded = data + bytes([pad_len] * pad_len)
            return encryptor.update(padded) + encryptor.finalize()

        crypt = _sm4.CryptSM4()
        crypt.set_key(self._key, _sm4.SM4_ENCRYPT)
        return crypt.crypt_ecb(data)

    def decrypt(self, enc_data: bytes) -> bytes:
        """Decrypt SM4-encrypted data."""
        if not HAS_GMSSL:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            cipher = Cipher(algorithms.AES(self._key), modes.ECB())
            decryptor = cipher.decryptor()
            padded = decryptor.update(enc_data) + decryptor.finalize()
            # Remove PKCS7 padding
            pad_len = padded[-1]
            return padded[:-pad_len]

        crypt = _sm4.CryptSM4()
        crypt.set_key(self._key, _sm4.SM4_DECRYPT)
        return crypt.crypt_ecb(enc_data)


def get_crypto_backend() -> str:
    """Get the current crypto backend ('standard' or 'gm')."""
    from app.config import settings
    backend = getattr(settings, "CRYPTO_BACKEND", "standard")
    if backend == "gm" and not HAS_GMSSL:
        logger.warning("CRYPTO_BACKEND=gm but gmssl not installed, falling back to standard")
        return "standard"
    return backend
