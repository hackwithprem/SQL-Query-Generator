import os
import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
import bcrypt
from cryptography.fernet import Fernet
from app.core.config import settings

# Derive a 32-byte key for Fernet symmetric encryption from JWT_SECRET_KEY
def _get_fernet_key() -> bytes:
    secret = getattr(settings, "JWT_SECRET_KEY", "sql-query-generator-production-secret-2026")
    key_bytes = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(key_bytes)

def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt with salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Encodes a signed JWT access token."""
    to_encode = data.copy()
    expire_minutes = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    
    to_encode.update({"exp": expire})
    secret = getattr(settings, "JWT_SECRET_KEY", "sql-query-generator-production-secret-2026")
    algorithm = getattr(settings, "JWT_ALGORITHM", "HS256")
    return jwt.encode(to_encode, secret, algorithm=algorithm)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a signed JWT access token."""
    try:
        secret = getattr(settings, "JWT_SECRET_KEY", "sql-query-generator-production-secret-2026")
        algorithm = getattr(settings, "JWT_ALGORITHM", "HS256")
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        return payload
    except (jwt.PyJWTError, Exception):
        return None

def encrypt_credential(secret_text: str) -> str:
    """Encrypts external credentials (e.g., database passwords) before storing."""
    if not secret_text:
        return ""
    f = Fernet(_get_fernet_key())
    return f.encrypt(secret_text.encode("utf-8")).decode("utf-8")

def decrypt_credential(cipher_text: str) -> str:
    """Decrypts encrypted external credentials."""
    if not cipher_text:
        return ""
    try:
        f = Fernet(_get_fernet_key())
        return f.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception:
        return ""
