"""
Import every model here so Base.metadata sees them — required for
Alembic's --autogenerate to detect all tables.
"""

from database.session import Base

from .chat_message import ChatMessage
from .document import Document
from .flashcard import Flashcard
from .quiz import Quiz, QuizQuestion
from .quiz_attempt import QuizAttempt
from .study_plan import StudyPlan
from .subject import Subject
from .user import User

__all__ = [
    "Base",
    "ChatMessage",
    "Document",
    "Flashcard",
    "Quiz",
    "QuizAttempt",
    "QuizQuestion",
    "StudyPlan",
    "Subject",
    "User",
]
