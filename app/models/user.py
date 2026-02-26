from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    hashed_password = Column(
        String(255),
        nullable=False
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False
    )
    is_superuser = Column(
        Boolean,
        default=False,
        nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_login = Column(
        DateTime(timezone=True),
        nullable=True
    )
    chat_history = relationship(
        "ChatHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"