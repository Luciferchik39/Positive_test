# src/services/minio_service.py
import io
from typing import Optional, Tuple
from minio import Minio
from minio.error import S3Error
import structlog
import os
from datetime import timedelta
from src.core.config import settings

logger = structlog.get_logger(__name__)


class MinIOService:
    """Сервис для работы с MinIO хранилищем."""

    def __init__(self) -> None:
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Проверить и создать bucket если не существует."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Bucket created: {self.bucket_name}")
            else:
                logger.info(f"Bucket already exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to create bucket: {e}")
            raise

    async def upload_file(
        self,
        file_path: str,
        file_data: bytes,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Загрузить файл в MinIO.

        Args:
            file_path: Путь в bucket (например, videos/uuid/video.mp4)
            file_data: Содержимое файла в байтах
            content_type: MIME тип файла

        Returns:
            str: URL или путь к загруженному файлу
        """
        try:
            file_size = len(file_data)
            file_stream = io.BytesIO(file_data)

            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                data=file_stream,
                length=file_size,
                content_type=content_type,
            )

            logger.info(
                "File uploaded to MinIO",
                bucket=self.bucket_name,
                path=file_path,
                size=file_size
            )

            return file_path

        except S3Error as e:
            logger.error(f"Failed to upload file to MinIO: {e}")
            raise

    async def download_file(self, file_path: str) -> bytes:
        """
        Скачать файл из MinIO.

        Args:
            file_path: Путь к файлу в bucket

        Returns:
            bytes: Содержимое файла
        """
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
            )

            file_data = response.read()
            response.close()
            response.release_conn()

            logger.info(
                "File downloaded from MinIO",
                bucket=self.bucket_name,
                path=file_path,
                size=len(file_data)
            )

            return file_data

        except S3Error as e:
            logger.error(f"Failed to download file from MinIO: {e}")
            raise

    async def delete_file(self, file_path: str) -> bool:
        """
        Удалить файл из MinIO.

        Args:
            file_path: Путь к файлу в bucket

        Returns:
            bool: True если файл удален
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
            )

            logger.info(
                "File deleted from MinIO",
                bucket=self.bucket_name,
                path=file_path
            )

            return True

        except S3Error as e:
            logger.error(f"Failed to delete file from MinIO: {e}")
            return False

    async def file_exists(self, file_path: str) -> bool:
        """
        Проверить существование файла в MinIO.

        Args:
            file_path: Путь к файлу в bucket

        Returns:
            bool: True если файл существует
        """
        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
            )
            return True
        except S3Error:
            return False

    async def get_file_url(self, file_path: str, expires: int = 3600) -> Optional[str]:
        try:
            # expires должен быть timedelta, а не int
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=file_path,
                expires=timedelta(seconds=expires),
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to generate file URL: {e}")
            return None