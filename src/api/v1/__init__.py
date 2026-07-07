# Positive_test/src/api/v1/endpoints/health.py
from typing import Any, Dict

import structlog
from fastapi import APIRouter
from src.core.config import settings
from src.core.database import check_database_connection

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    logger.info("Health check requested")
    return {"status": "ok", "service": "positive-video-processing"}


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check for all services."""
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "services": {
            "database": False,
            "kafka": False,
            "minio": False,
            "redis": False,
        },
    }

    # Check database
    try:
        db_healthy: bool = await check_database_connection()
        health_status["services"]["database"] = db_healthy
        if not db_healthy:
            health_status["status"] = "degraded"
        logger.info("Database health check", healthy=db_healthy)
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        health_status["status"] = "unhealthy"

    # Check Kafka (basic connectivity check)
    try:
        from aiokafka import AIOKafkaProducer

        producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
        )
        await producer.start()
        await producer.stop()
        health_status["services"]["kafka"] = True
        logger.info("Kafka health check", healthy=True)
    except Exception as e:
        logger.error("Kafka health check failed", error=str(e))
        health_status["status"] = "degraded"

    # Check MinIO
    try:
        import boto3

        s3_client = boto3.client(
            "s3",
            endpoint_url=settings.minio_endpoint_url,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name="us-east-1",
        )
        s3_client.list_buckets()
        health_status["services"]["minio"] = True
        logger.info("MinIO health check", healthy=True)
    except Exception as e:
        logger.error("MinIO health check failed", error=str(e))
        health_status["status"] = "degraded"

    # Check Redis
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.close()
        health_status["services"]["redis"] = True
        logger.info("Redis health check", healthy=True)
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        health_status["status"] = "degraded"

    return health_status
