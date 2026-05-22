"""Authentication endpoints for user registration, login, and token refresh."""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api.auth.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from api.auth.models import RefreshToken, User, init_auth_db
from api.auth.schemas import (
    MessageResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserDetailResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

DATABASE_URL = "sqlite:///./storage/auth.db"


def get_db():
    """Get database session."""
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Get database session directly."""
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


@router.post("/register", response_model=UserResponse)
def register(request: UserRegisterRequest):
    """Register a new user."""
    db = get_db_session()

    existing_email = db.query(User).filter(User.email == request.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    existing_username = db.query(User).filter(User.username == request.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    user_id = str(uuid.uuid4())
    hashed_password = hash_password(request.password)

    user = User(
        id=user_id,
        email=request.email,
        username=request.username,
        hashed_password=hashed_password,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    return user


@router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest):
    """Login user and return access/refresh tokens."""
    db = get_db_session()

    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.hashed_password):
        db.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    user.last_login = datetime.utcnow()
    db.commit()

    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    db.close()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    payload = verify_token(request.refresh_token, token_type="refresh")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    db = get_db_session()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access_token = create_access_token(data={"sub": user.id})
    new_refresh_token = create_refresh_token(data={"sub": user.id})

    db.close()

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=1800,
    )


@router.get("/me", response_model=UserDetailResponse)
def get_current_user_info(user_id: str):
    """Get current user info (requires authentication)."""
    db = get_db_session()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.close()
    return user


@router.post("/logout", response_model=MessageResponse)
def logout(user_id: str):
    """Logout user (revoke tokens)."""
    return MessageResponse(message="Successfully logged out")
