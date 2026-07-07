# Positive_test/src/api/v1/endpoints/health.py
from typing import Dict

import structlog
from fastapi import APIRouter

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    logger.info("Health check requested")
    return {"status": "ok", "service": "positive-video-processing"}
