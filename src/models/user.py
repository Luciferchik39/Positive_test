# src/models/user.py
from sqlalchemy import Column, String, UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100))

    # Отношения
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")