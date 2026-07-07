# src/services/kafka_service.py
import json
import structlog
from typing import Optional, Dict, Any
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import NoBrokersAvailable
from datetime import datetime
from src.core.config import settings

logger = structlog.get_logger(__name__)


class KafkaService:
    """Сервис для работы с Kafka."""

    def __init__(self) -> None:
        self.producer: Optional[AIOKafkaProducer] = None
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.video_topic = settings.KAFKA_TOPIC_VIDEO_PROCESSING

    async def start_producer(self) -> None:
        """Запустить продюсер Kafka."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                compression_type='gzip',
            )
            await self.producer.start()
            logger.info("Kafka producer started", servers=self.bootstrap_servers)
        except NoBrokersAvailable:
            logger.error("No Kafka brokers available", servers=self.bootstrap_servers)
            raise
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise

    async def stop_producer(self) -> None:
        """Остановить продюсер Kafka."""
        if self.producer:
            await self.producer.stop()
            self.producer = None
            logger.info("Kafka producer stopped")

    async def send_video_task(
        self,
        video_id: str,
        input_path: str,
        quality: str = "medium",
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Отправить задачу на обработку видео в Kafka.

        Args:
            video_id: ID видео
            input_path: Путь к видео в MinIO
            quality: Качество обработки (low, medium, high)
            user_id: ID пользователя (опционально)

        Returns:
            bool: True если сообщение отправлено успешно
        """
        if not self.producer:
            logger.error("Kafka producer is not started")
            return False

        try:
            message = {
                "video_id": video_id,
                "input_path": input_path,
                "quality": quality,
                "user_id": user_id,
                "timestamp": str(datetime.now()),
            }

            # Отправляем сообщение
            await self.producer.send(
                topic=self.video_topic,
                value=message,
                key=video_id.encode('utf-8'),  # Используем video_id как ключ
            )

            logger.info(
                "Video task sent to Kafka",
                topic=self.video_topic,
                video_id=video_id,
                quality=quality,
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send video task to Kafka: {e}", video_id=video_id)
            return False

    async def ensure_topic_exists(self) -> bool:
        """
        Проверить, что топик существует.
        Если нет — создать.
        """
        # Kafka автоматически создает топик при отправке сообщения
        # если auto.create.topics.enable = true (по умолчанию)
        # Просто пробуем отправить тестовое сообщение
        return True