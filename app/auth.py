"""JWT session auth with hardcoded credentials for now"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Request

from app.config import JWT_SECRET

# Credentials are hardcoded for now
VALID_EMAIL = "demo@example.com"
VALID_PASSWORD = "DemoPassword123!"
USER_NAME = "Example User"

# Session settings: the cookie name, the JWT signing algorithm, and how long a login lasts.
COOKIE_NAME = "session"
JWT_ALGORITHM = "HS256"
SESSION_HOURS = 12


def check_credentials(email: str, password: str) -> bool:
    """string comparison against the hardcoded credentials."""
    return email == VALID_EMAIL and password == VALID_PASSWORD


def create_token() -> str:
    """Issue a signed JWT carrying the user's identity and an expiry."""
    now = datetime.now(timezone.utc)
    # The payload is the data stored inside the token: who the user is,
    # when it was issued ("iat"), and when it expires ("exp").
    payload = {
        "email": VALID_EMAIL,
        "name": USER_NAME,
        "iat": now,
        "exp": now + timedelta(hours=SESSION_HOURS),
    }
    # Sign the payload with the secret key so the token cannot be forged.
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(request: Request) -> dict | None:
    """Decode the session cookie's JWT, or return None if missing/invalid/expired."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        # No cookie at all — the visitor has not logged in.
        return None
    try:
        # Check the signature and expiry, then hand back the stored payload.
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        # Token is invalid.
        return None


def require_user(request: Request) -> dict:
    """Requires a valid login before a protected route runs; rejects requests without one."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
