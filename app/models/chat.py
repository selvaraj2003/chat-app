from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Index,
    Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    session_id = Column(
        String(100),
        nullable=False,
        index=True,
        doc="Chat session/group id"
    )
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)

    model_name = Column(
        String(50),
        nullable=False,
        default="llama3",
        doc="Ollama model name"
    )
    temperature = Column(
        Float,
        nullable=True,
        default=0.7
    )

    tokens_used = Column(
        Integer,
        nullable=True,
        doc="Total tokens consumed by LLM"
    )
    latency_ms = Column(
        Integer,
        nullable=True,
        doc="AI response time in milliseconds"
    )
    is_success = Column(
        Boolean,
        default=True,
        nullable=False
    )
    error_message = Column(
        Text,
        nullable=True
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
    user = relationship(
        "User",
        back_populates="chat_history"
    )
    __table_args__ = (
        Index("idx_chat_user_session", "user_id", "session_id"),
        Index("idx_chat_created_at", "created_at"),
    )