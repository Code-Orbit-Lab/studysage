"""StudyPlan model. Owner: Sumit"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from database.session import Base


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    deadline = Column(Date, nullable=False)
    hours_per_day = Column(Numeric, nullable=False)
    plan_json = Column(
        JSONB, nullable=False
    )  # day-by-day schedule, see ai-service planner output
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="study_plans")
