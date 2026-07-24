"""ChatMessage model — persisted RAG chat turns. Owner: Sumit"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from database.session import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        # Matches docs/05_Database/database.md — history is always fetched
        # "latest N messages for this subject", so this composite index is
        # the one that actually gets used, not two separate single-column ones.
        Index("ix_chat_messages_subject_id_created_at", "subject_id", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String, nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    citations = Column(JSONB, nullable=True)  # [{document_id, page, snippet}, ...]
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    subject = relationship("Subject", back_populates="chat_messages")
