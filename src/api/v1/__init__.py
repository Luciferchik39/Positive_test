# src/api/v1/__init__.py
from fastapi import APIRouter
from .endpoints import health, videos

router = APIRouter(prefix="/api/v1")

router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(videos.router, prefix="/videos", tags=["Videos"])