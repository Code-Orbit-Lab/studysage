"""Subject model. Owner: Sumit"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database.session import Base


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    documents = relationship(
        "Document", back_populates="subject", cascade="all, delete-orphan"
    )
    chat_messages = relationship(
        "ChatMessage", back_populates="subject", cascade="all, delete-orphan"
    )
    quizzes = relationship(
        "Quiz", back_populates="subject", cascade="all, delete-orphan"
    )
    flashcards = relationship(
        "Flashcard", back_populates="subject", cascade="all, delete-orphan"
    )
