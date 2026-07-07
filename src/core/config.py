# Positive_test/src/core/config.py
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ==================== Application ====================
    DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    PROJECT_NAME: str = "Positive Video Processing"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api/v1"

    # ==================== CORS ====================
    CORS_ALLOWED_ORIGINS: list[str] = ["*"]  # В продакшене заменить на конкретные домены
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # ==================== PostgreSQL ====================
    POSTGRES_USER: str = "positive_user"
    POSTGRES_PASSWORD: str = "positive_pass"
    POSTGRES_DB: str = "positive_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # ==================== Kafka ====================
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_VIDEO_PROCESSING: str = "video_processing"
    KAFKA_TOPIC_VIDEO_RESULTS: str = "video_processing_results"
    KAFKA_CONSUMER_GROUP: str = "video_processor_group"
    KAFKA_MAX_POLL_RECORDS: int = 10

    # ==================== MinIO ====================
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "positive-videos"
    MINIO_SECURE: bool = False

    # ==================== Redis ====================
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 час

    # ==================== JWT (для аутентификации) ====================
    SECRET_KEY: str = "your-secret-key-change-in-production"  # Обязательно изменить!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==================== Rate Limiting ====================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # ==================== Логирование ====================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" или "console"

    # ==================== Обработка видео ====================
    MAX_VIDEO_SIZE_MB: int = 500
    SUPPORTED_VIDEO_FORMATS: list[str] = ["mp4", "avi", "mov", "mkv", "webm"]
    ALLOWED_VIDEO_CODECS: list[str] = ["h264", "h265", "vp9", "av1"]
    THUMBNAIL_WIDTH: int = 320
    THUMBNAIL_HEIGHT: int = 180

    # ==================== Worker ====================
    WORKER_POLL_INTERVAL: int = 1  # секунды
    WORKER_MAX_RETRIES: int = 3
    WORKER_RETRY_DELAY: int = 5  # секунды

    @property
    def database_url(self) -> str:
        """Construct database URL from components if not provided directly."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def minio_endpoint_url(self) -> str:
        """Construct full MinIO endpoint URL."""
        protocol: str = "https" if self.MINIO_SECURE else "http"
        return f"{protocol}://{self.MINIO_ENDPOINT}"

    @property
    def kafka_bootstrap_servers_list(self) -> list[str]:
        """Convert Kafka bootstrap servers string to list."""
        return [s.strip() for s in self.KAFKA_BOOTSTRAP_SERVERS.split(",")]


# Create global settings instance
settings = Settings()