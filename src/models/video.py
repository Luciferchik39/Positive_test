# src/models/video.py
from sqlalchemy import Column, String, UUID, Enum, DateTime, Text, Integer, Float
import uuid
from .base import Base, TimestampMixin
import enum


class VideoStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoQuality(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Video(Base, TimestampMixin):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    original_filename = Column(String(255), nullable=False)

    input_path = Column(String(500), nullable=False)
    output_path = Column(String(500), nullable=True)

    file_size = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    fps = Column(Float, nullable=True)

    quality: VideoQuality = Column(  # type: ignore[assignment]
        Enum(VideoQuality), default=VideoQuality.MEDIUM, nullable=True
    )
    status: VideoStatus = Column(  # type: ignore[assignment]
        Enum(VideoStatus), default=VideoStatus.PENDING, nullable=False
    )
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    processed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Video {self.title} ({self.status})>"


__all__ = ["Video", "VideoStatus", "VideoQuality"]