# src/models/video.py
from sqlalchemy import Column, String, UUID, Enum, DateTime, ForeignKey, Text, Integer, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
import uuid
from .base import Base, TimestampMixin
import enum


class VideoStatus(str, enum.Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VideoQuality(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UHD = "uhd"


class Video(Base, TimestampMixin):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(200), nullable=False)
    description = Column(Text)
    original_filename = Column(String(255), nullable=False)

    input_path = Column(String(500), nullable=False)
    output_path = Column(String(500))
    thumbnail_path = Column(String(500))

    file_size = Column(Integer)
    duration = Column(Float)
    width = Column(Integer)
    height = Column(Integer)
    fps = Column(Float)
    codec = Column(String(50))

    quality = Column(Enum(VideoQuality), default=VideoQuality.MEDIUM)
    processing_options = Column(JSONB, default={})

    status = Column(Enum(VideoStatus), default=VideoStatus.PENDING, nullable=False, index=True)
    progress = Column(Integer, default=0)
    error_message = Column(Text)

    processed_at = Column(DateTime)

    user = relationship("User", back_populates="videos")