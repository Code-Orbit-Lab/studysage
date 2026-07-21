"""
Import every model here so Base.metadata sees them — required for
Alembic's --autogenerate to detect all tables.
"""
from database.session import Base
from .user import User
from .subject import Subject
from .document import Document

__all__ = ["Base", "User", "Subject", "Document"]