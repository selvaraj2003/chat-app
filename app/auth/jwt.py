from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from jose.exceptions import JWTError

from app.core.config import settings


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT access token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings["ACCESS_TOKEN_EXPIRE_MINUTES"]
        )

    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    encoded_jwt = jwt.encode(
        payload,
        settings["SECRET_KEY"],
        algorithm=settings["ALGORITHM"],
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and validate JWT token
    """
    try:
        payload = jwt.decode(
            token,
            settings["SECRET_KEY"],
            algorithms=[settings["ALGORITHM"]],
        )
        return payload
    except JWTError:
        raise ValueError("Invalid or expired token")