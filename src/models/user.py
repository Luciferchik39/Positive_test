# src/models/user.py
import uuid

from sqlalchemy import UUID, Column, String
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100))

    # Отношения
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")
