import base64
import hashlib
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Optional

import bcrypt
from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Returns False on mismatch *or* when the hash is malformed/invalid,
    preventing user enumeration via 500 vs 401 responses (FW-C04).
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    # Ensure "tv" (token_version) is present; default to 0 if caller didn't set it
    if "tv" not in to_encode:
        to_encode["tv"] = 0
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def get_encryption_key() -> bytes:
    key = os.environ.get("ENCRYPTION_KEY", settings.ENCRYPTION_KEY)
    return base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest()[:32])


def encrypt(text: str) -> str:
    f = Fernet(get_encryption_key())
    return f.encrypt(text.encode()).decode()


def decrypt(encrypted_text: str) -> str:
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_text.encode()).decode()


# ---------------------------------------------------------------------------
# Crypto backend adapter
# ---------------------------------------------------------------------------

def _get_sm4_key() -> bytes:
    """Derive SM4 key from SECRET_KEY."""
    key = settings.SECRET_KEY.encode()
    # SM4 needs exactly 16 bytes
    return hashlib.sha256(key).digest()[:16]


def hash_password_crypto(password: str) -> str:
    """Hash password using the configured crypto backend."""
    from app.core.sm_crypto import get_crypto_backend, SM3Helper
    if get_crypto_backend() == "gm":
        return SM3Helper.hash_password(password)
    return get_password_hash(password)


def verify_password_crypto(plain: str, hashed: str) -> bool:
    """Verify password using the configured crypto backend."""
    from app.core.sm_crypto import get_crypto_backend, SM3Helper
    if get_crypto_backend() == "gm" and "$" in hashed:
        return SM3Helper.verify_password(plain, hashed)
    return verify_password(plain, hashed)


def encrypt_data_crypto(plaintext: str) -> str:
    """Encrypt data using the configured crypto backend."""
    from app.core.sm_crypto import get_crypto_backend, SM4Helper
    if get_crypto_backend() == "gm":
        key = _get_sm4_key()
        sm4 = SM4Helper(key)
        encrypted = sm4.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()
    return encrypt(plaintext)


def decrypt_data_crypto(ciphertext: str) -> str:
    """Decrypt data using the configured crypto backend."""
    from app.core.sm_crypto import get_crypto_backend, SM4Helper
    if get_crypto_backend() == "gm":
        key = _get_sm4_key()
        sm4 = SM4Helper(key)
        encrypted = base64.b64decode(ciphertext)
        return sm4.decrypt(encrypted).decode()
    return decrypt(ciphertext)
