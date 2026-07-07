# src/worker.py
import json
import structlog
import os
import time
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from kafka import KafkaConsumer, KafkaProducer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from src.core.config import settings
from src.models import Video, VideoStatus
from src.services.minio_service import MinIOService
from src.services.video_processor import VideoProcessor

logger = structlog.get_logger(__name__)


class VideoWorker:
    def __init__(self) -> None:
        self.running: bool = True
        self.consumer: Optional[KafkaConsumer] = None
        self.producer: Optional[KafkaProducer] = None

        self.engine = create_async_engine(settings.database_url, echo=True)
        self.async_session = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

        self.minio = MinIOService()
        self.processor = VideoProcessor()

    def connect_kafka(self) -> bool:
        """Подключение к Kafka"""
        try:
            self.consumer = KafkaConsumer(
                settings.KAFKA_TOPIC_VIDEO_PROCESSING,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='video-worker-group'
            )

            self.producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )

            logger.info("Connected to Kafka")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            return False

    async def process_video(self, video_id: str) -> None:
        """Обработка видео"""
        logger.info("Processing video", video_id=video_id)

        async with self.async_session() as session:
            result = await session.execute(
                select(Video).where(Video.id == video_id)  # type: ignore
            )
            video: Optional[Video] = result.scalar_one_or_none()

            if not video:
                logger.error("Video not found", video_id=video_id)
                return

            try:
                # Обновляем статус
                video.status = VideoStatus.PROCESSING  # type: ignore[assignment]
                video.progress = 0  # type: ignore[assignment]
                await session.commit()

                logger.info("Downloading video from MinIO", video_id=video_id)
                input_data = await self.minio.download_file(video.input_path)

                logger.info("Processing video", video_id=video_id)
                output_data, metadata = await self.processor.process(
                    input_data,
                    quality="medium",
                    video_id=video_id
                )

                output_path = f"processed/{video_id}/output.mp4"
                logger.info("Uploading result to MinIO", video_id=video_id)
                await self.minio.upload_file(output_path, output_data)

                # Обновляем запись в БД
                video.output_path = output_path  # type: ignore[assignment]
                video.status = VideoStatus.COMPLETED  # type: ignore[assignment]
                video.progress = 100  # type: ignore[assignment]
                video.processed_at = datetime.now()  # type: ignore[assignment]
                video.duration = metadata.get('duration')  # type: ignore[assignment]
                video.width = metadata.get('width')  # type: ignore[assignment]
                video.height = metadata.get('height')  # type: ignore[assignment]
                video.fps = metadata.get('fps')  # type: ignore[assignment]

                await session.commit()

                logger.info("Video processed successfully", video_id=video_id)

                if self.producer:
                    self.producer.send('video-processing-results', {
                        'video_id': video_id,
                        'status': 'completed',
                        'output_path': output_path
                    })

            except Exception as e:
                logger.error(f"Error processing video: {e}", video_id=video_id)
                video.status = VideoStatus.FAILED  # type: ignore[assignment]
                video.error_message = str(e)  # type: ignore[assignment]
                await session.commit()

    async def run(self) -> None:
        """Основной цикл worker"""
        if not self.connect_kafka():
            return

        logger.info("Worker started, waiting for tasks...")

        while self.running:
            try:
                if self.consumer is None:
                    break

                messages = self.consumer.poll(timeout_ms=1000)

                for topic_partition, records in messages.items():
                    for record in records:
                        task: Dict[str, Any] = record.value
                        video_id: Optional[str] = task.get('video_id')

                        if video_id:
                            await self.process_video(video_id)

                await asyncio.sleep(0.1)

            except KeyboardInterrupt:
                logger.info("Shutting down worker...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(5)

        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.close()
        await self.engine.dispose()


async def main() -> None:
    worker = VideoWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())