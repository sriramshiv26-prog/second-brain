"""Database models for authentication."""

from datetime import datetime
from sqlalchemy import Column, DateTime, String, create_engine
from sqlalchemy.orm import Session, declarative_base

Base = declarative_base()


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.username}>"


class RefreshToken(Base):
    """Refresh token blacklist model for token rotation."""

    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    token_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<RefreshToken {self.user_id}>"


def get_db_connection():
    """Get SQLite database connection."""
    db_url = "sqlite:///./storage/auth.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    return engine


def init_auth_db():
    """Initialize authentication database."""
    engine = get_db_connection()
    Base.metadata.create_all(bind=engine)
