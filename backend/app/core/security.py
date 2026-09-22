from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from app.core.config import settings

password_hash = PasswordHash.recommended()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30


def hash_password(password: str) -> str:
    """Hash a plaintext password using the recommended password hasher."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored password hash."""
    try:
        return password_hash.verify(password, hashed_password)
    except UnknownHashError:
        return False


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": subject, "type": token_type, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived access token."""
    return _create_token(
        subject,
        "access",
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(subject: str) -> str:
    """Create a long-lived refresh token."""
    return _create_token(subject, "refresh", timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


def _decode_token(token: str, expected_type: str) -> str:
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Expected {expected_type} token")
    subject = payload.get("sub")
    if subject is None:
        raise jwt.InvalidTokenError("Token missing subject")
    return str(subject)


def decode_access_token(token: str) -> str:
    """Validate an access token and return its subject."""
    return _decode_token(token, "access")


def decode_refresh_token(token: str) -> str:
    """Validate a refresh token and return its subject."""
    return _decode_token(token, "refresh")