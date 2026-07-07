# src/api/v1/endpoints/videos.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Any, Dict
import uuid
import structlog
import os

from src.core.database import get_db
from src.models import Video, VideoStatus
from src.schemas.video import VideoResponse, VideoListResponse, VideoUploadResponse

logger = structlog.get_logger(__name__)
router = APIRouter()

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=VideoUploadResponse, status_code=201)
async def upload_video(
    title: str = Form(..., min_length=1, max_length=200),
    description: Optional[str] = Form(None),
    file: UploadFile = File(..., description="Видео файл (mp4, avi, mov, mkv, webm)"),
    db: AsyncSession = Depends(get_db)
) -> VideoUploadResponse:
    """Загрузить видео для обработки."""
    logger.info("Uploading video", title=title, filename=file.filename)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
        )

    video_id = uuid.uuid4()
    input_filename = f"{video_id}{ext}"
    input_path = f"uploads/{input_filename}"

    file_path = os.path.join(UPLOAD_DIR, input_filename)
    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    file_size = len(content)

    video = Video(
        id=video_id,
        title=title,
        description=description,
        original_filename=file.filename,
        input_path=input_path,
        file_size=file_size,
        status=VideoStatus.PENDING,
        progress=0
    )

    db.add(video)
    await db.commit()
    await db.refresh(video)

    logger.info("Video uploaded successfully", video_id=str(video_id))

    return VideoUploadResponse(
        id=video.id,
        title=video.title,
        status=video.status,
        message="Video uploaded successfully. Processing will start shortly."
    )


@router.get("/", response_model=VideoListResponse)
async def get_videos(
    status: Optional[VideoStatus] = Query(None, description="Фильтр по статусу"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> VideoListResponse:
    """Получить список всех видео."""
    logger.info("Getting videos list", status=status, skip=skip, limit=limit)

    query = select(Video)
    if status is not None:
        query = query.where(Video.status == status)  # type: ignore[arg-type]

    query = query.offset(skip).limit(limit).order_by(Video.created_at.desc())

    result = await db.execute(query)
    videos = result.scalars().all()

    count_query = select(func.count()).select_from(Video)
    if status is not None:
        count_query = count_query.where(Video.status == status)  # type: ignore[arg-type]
    total = await db.scalar(count_query)

    return VideoListResponse(
        items=videos,
        total=total or 0,
        skip=skip,
        limit=limit
    )


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Получить информацию о видео."""
    logger.info("Getting video", video_id=str(video_id))

    result = await db.execute(
        select(Video).where(Video.id == video_id)  # type: ignore[arg-type]
    )
    video: Optional[Video] = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return video


@router.get("/{video_id}/status")
async def get_video_status(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Получить статус обработки видео."""
    logger.info("Getting video status", video_id=str(video_id))

    result = await db.execute(
        select(Video).where(Video.id == video_id)  # type: ignore[arg-type]
    )
    video: Optional[Video] = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return {
        "id": str(video.id),
        "title": video.title,
        "status": video.status.value,
        "progress": video.progress,
        "error_message": video.error_message,
        "processed_at": video.processed_at
    }


@router.get("/{video_id}/download")
async def download_video(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """Скачать обработанное видео."""
    logger.info("Downloading video", video_id=str(video_id))

    result = await db.execute(
        select(Video).where(Video.id == video_id)  # type: ignore[arg-type]
    )
    video: Optional[Video] = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.status != VideoStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Video not processed yet. Status: {video.status.value}"
        )

    if not video.output_path:
        raise HTTPException(status_code=404, detail="Processed video not found")

    file_path = os.path.join(UPLOAD_DIR, os.path.basename(video.input_path))

    if not os.path.exists(file_path):
        processed_path = os.path.join(UPLOAD_DIR, f"processed_{os.path.basename(video.input_path)}")
        if os.path.exists(processed_path):
            file_path = processed_path
        else:
            raise HTTPException(status_code=404, detail="Video file not found")

    filename = str(video.original_filename) if video.original_filename else f"video_{video_id}.mp4"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="video/mp4"
    )


@router.delete("/{video_id}", status_code=204)
async def delete_video(
    video_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Удалить видео и все связанные файлы."""
    logger.info("Deleting video", video_id=str(video_id))

    result = await db.execute(
        select(Video).where(Video.id == video_id)  # type: ignore[arg-type]
    )
    video: Optional[Video] = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    input_file = os.path.join(UPLOAD_DIR, os.path.basename(video.input_path))
    if os.path.exists(input_file):
        os.remove(input_file)

    processed_file = os.path.join(UPLOAD_DIR, f"processed_{os.path.basename(video.input_path)}")
    if os.path.exists(processed_file):
        os.remove(processed_file)

    await db.delete(video)
    await db.commit()

    logger.info("Video deleted", video_id=str(video_id))
    return None