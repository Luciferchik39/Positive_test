# src/worker.py
import json
import logging
import time
from typing import Dict, Any

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable
import os
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(self):
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
        self.consumer = None
        self.producer = None
        self.running = True

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, signum=None, frame=None):
        logger.info("Received shutdown signal, stopping worker...")
        self.running = False

    def connect(self):
        """Connect to Kafka"""
        retries = 10
        while retries > 0 and self.running:
            try:
                logger.info(f"Connecting to Kafka at {self.bootstrap_servers}")
                self.consumer = KafkaConsumer(
                    'video-processing-tasks',  # Топик для задач
                    bootstrap_servers=self.bootstrap_servers,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='earliest',
                    enable_auto_commit=True,
                    group_id='video-processor-group'
                )

                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )

                logger.info("Successfully connected to Kafka")
                return True

            except NoBrokersAvailable:
                logger.warning(f"No brokers available. Retrying in 5s... (retries left: {retries})")
                time.sleep(5)
                retries -= 1
            except Exception as e:
                logger.error(f"Error connecting to Kafka: {e}")
                time.sleep(5)
                retries -= 1

        logger.error("Failed to connect to Kafka after retries")
        return False

    def process_video(self, task: Dict[str, Any]):
        """Обработка видео задачи"""
        video_id = task.get('video_id')
        video_path = task.get('video_path')
        user_id = task.get('user_id')

        logger.info(f"Processing video {video_id} for user {user_id}")

        try:
            # 🔥 ЗДЕСЬ ВАША ЛОГИКА ОБРАБОТКИ ВИДЕО 🔥
            # Например:
            # 1. Загрузка видео из MinIO
            # 2. Обработка (конвертация, обрезка, анализ и т.д.)
            # 3. Сохранение результата обратно в MinIO

            time.sleep(5)  # Имитация обработки

            # Отправка результата
            result = {
                'video_id': video_id,
                'status': 'completed',
                'result_path': f'/processed/{video_id}_processed.mp4'
            }

            self.producer.send('video-processing-results', result)
            logger.info(f"Video {video_id} processed successfully")

        except Exception as e:
            logger.error(f"Error processing video {video_id}: {e}")
            # Отправка ошибки
            self.producer.send('video-processing-results', {
                'video_id': video_id,
                'status': 'failed',
                'error': str(e)
            })

    def run(self):
        """Основной цикл воркера"""
        if not self.connect():
            logger.error("Could not connect to Kafka, exiting...")
            sys.exit(1)

        logger.info("Worker started, waiting for tasks...")

        while self.running:
            try:
                # Получаем сообщения из Kafka
                messages = self.consumer.poll(timeout_ms=1000)

                for topic_partition, records in messages.items():
                    for record in records:
                        task = record.value
                        logger.info(f"Received task: {task}")
                        self.process_video(task)

                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(5)


if __name__ == "__main__":
    processor = VideoProcessor()
    processor.run()