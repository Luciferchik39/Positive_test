# src/schemas/video.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.models import VideoStatus


class VideoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class VideoResponse(VideoBase):
    id: UUID
    original_filename: str
    input_path: str
    output_path: Optional[str]
    file_size: Optional[int]
    duration: Optional[float]
    width: Optional[int]
    height: Optional[int]
    fps: Optional[float]
    status: VideoStatus
    progress: int
    error_message: Optional[str]
    processed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    items: List[VideoResponse]
    total: int
    skip: int
    limit: int


class VideoUploadResponse(BaseModel):
    id: UUID
    title: str
    status: VideoStatus
    message: str
