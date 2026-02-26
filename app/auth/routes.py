from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.database import get_db
from app.models.user import User
from app.auth.schemas import (
    UserCreate,
    UserLogin,
    TokenResponse,
)
from app.auth.jwt import create_access_token
from app.core.security import verify_password, hash_password
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


# =========================
# Register
# =========================
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    # Check email
    existing_email = db.query(User).filter(User.email == payload.email).first()
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Check username
    existing_username = db.query(User).filter(User.username == payload.username).first()
    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_active=True,
        is_verified=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User registered successfully"
    }


# =========================
# Login
# =========================
@router.post("/login", response_model=TokenResponse)
def login_user(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=settings["ACCESS_TOKEN_EXPIRE_MINUTES"]),
    )

    user.last_login = settings.utcnow()
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }