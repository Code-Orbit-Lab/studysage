"""User model. Owner: Sumit"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID

from database.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)  # null if Google-OAuth-only
    name = Column(String, nullable=False)
    auth_provider = Column(String, nullable=False, default="email")  # "email" | "google"
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))