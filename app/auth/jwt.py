from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from jose.exceptions import JWTError

from app.core.config import settings


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token."""
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings["ACCESS_TOKEN_EXPIRE_MINUTES"])
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings["SECRET_KEY"], algorithm=settings["ALGORITHM"])


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    Raises ValueError on failure so callers can convert to HTTP 401.
    """
    try:
        return jwt.decode(
            token,
            settings["SECRET_KEY"],
            algorithms=[settings["ALGORITHM"]],
        )
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc