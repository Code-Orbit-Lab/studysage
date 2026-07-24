"""
Import every model here so Base.metadata sees them — required for
Alembic's --autogenerate to detect all tables.
"""
from database.session import Base
from .user import User
from .subject import Subject
from .document import Document
from .chat_message import ChatMessage
from .quiz import Quiz, QuizQuestion
from .quiz_attempt import QuizAttempt
from .flashcard import Flashcard
from .study_plan import StudyPlan

__all__ = [
    "Base",
    "User",
    "Subject",
    "Document",
    "ChatMessage",
    "Quiz",
    "QuizQuestion",
    "QuizAttempt",
    "Flashcard",
    "StudyPlan",
]