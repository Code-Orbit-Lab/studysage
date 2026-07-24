"""Document model — uploaded file metadata. Owner: Sumit"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database.session import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # "pdf" | "docx" | "pptx" | "image"
    storage_path = Column(String, nullable=False)
    status = Column(
        String, nullable=False, default="uploaded"
    )  # uploaded|processing|ready|failed
    page_count = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    subject = relationship("Subject", back_populates="documents")
