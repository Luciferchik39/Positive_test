# Positive_test/scripts/init_minio.py
"""
Script to initialize MinIO bucket on first run.
"""
import sys
from typing import Any

import boto3
from botocore.exceptions import ClientError

from src.core.config import settings


def create_bucket_if_not_exists() -> bool:
    """Create MinIO bucket if it doesn't exist."""
    try:
        # Create S3 client for MinIO
        s3_client: Any = boto3.client(
            "s3",
            endpoint_url=settings.minio_endpoint_url,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name="us-east-1",
        )

        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=settings.MINIO_BUCKET_NAME)
            print(f"Bucket '{settings.MINIO_BUCKET_NAME}' already exists.")
            return True
        except ClientError:
            # Bucket doesn't exist, create it
            s3_client.create_bucket(Bucket=settings.MINIO_BUCKET_NAME)
            print(f"Bucket '{settings.MINIO_BUCKET_NAME}' created successfully.")
            return True

    except Exception as e:
        print(f"Error initializing MinIO bucket: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    success = create_bucket_if_not_exists()
    sys.exit(0 if success else 1)