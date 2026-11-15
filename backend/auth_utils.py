"""
auth_utils.py – Cryptographic utilities for Triad Care authentication.

Provides:
  - Argon2id password hashing / verification
  - JWT access-token creation and validation
  - Opaque refresh-token generation (raw secret + stored hash)
  - CSRF token generation
"""
import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

# ---------------------------------------------------------------------------
# Configuration (read from environment; must be set before production use)
# ---------------------------------------------------------------------------
SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION_min32chars!!")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
REFRESH_TOKEN_EXPIRE_DAYS: int = 7
ISSUER: str = "triadcare"
AUDIENCE: str = "triadcare-api"

# ---------------------------------------------------------------------------
# Argon2id password hasher – parameters approved by SECURITY_AUDIT.md
#   m=65536 (64 MiB), t=3, p=4
# ---------------------------------------------------------------------------
_ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(plaintext: str) -> str:
    """Hash a plaintext password using Argon2id.  Returns the full Argon2 hash string."""
    return _ph.hash(plaintext)


def verify_password(hashed: str, plaintext: str) -> bool:
    """Return True if plaintext matches the stored Argon2id hash, False otherwise."""
    try:
        return _ph.verify(hashed, plaintext)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_needs_rehash(hashed: str) -> bool:
    """Return True if the stored hash should be regenerated (parameter upgrade)."""
    return _ph.check_needs_rehash(hashed)


# ---------------------------------------------------------------------------
# JWT access tokens
# ---------------------------------------------------------------------------

def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token with minimal claims.

    Claims: sub (user ID as string), type, jti, iat, exp, iss, aud.
    Roles and permissions are NOT embedded; they must be fetched from DB.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": str(user_id),
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": expire,
        "iss": ISSUER,
        "aud": AUDIENCE,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Raises jwt.exceptions.* on any validation failure.
    Callers must catch these and return HTTP 401.
    """
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        issuer=ISSUER,
        audience=AUDIENCE,
        options={"require": ["sub", "type", "jti", "iat", "exp"]},
    )


# ---------------------------------------------------------------------------
# Opaque refresh tokens
# ---------------------------------------------------------------------------

def generate_refresh_token() -> tuple[str, str]:
    """Generate a cryptographically random refresh token.

    Returns:
        (plain_token, token_hash)
        - plain_token: 48-byte URL-safe secret returned to the client via cookie.
        - token_hash:  SHA-256 hex digest stored in the database.
    """
    plain = secrets.token_urlsafe(48)
    h = hashlib.sha256(plain.encode()).hexdigest()
    return plain, h


def hash_refresh_token(plain: str) -> str:
    """Return the SHA-256 hex digest of a plain refresh token string."""
    return hashlib.sha256(plain.encode()).hexdigest()


def new_family_id() -> str:
    """Return a new UUID4 string to identify a refresh-token family (login session)."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# CSRF tokens
# ---------------------------------------------------------------------------

def generate_csrf_token() -> str:
    """Return a 32-byte URL-safe CSRF token."""
    return secrets.token_urlsafe(32)


def refresh_token_expires_at() -> datetime:
    """Return the expiry datetime for a new refresh token (UTC)."""
    return datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
