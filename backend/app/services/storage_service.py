import boto3
from botocore.exceptions import ClientError

from backend.app.config import get_settings

settings = get_settings()


def get_s3_client():
    """Get a boto3 S3 client configured for MinIO."""
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name="us-east-1",
    )


def ensure_bucket_exists() -> None:
    """Create the finsight-documents bucket if it doesn't exist.

    Called on FastAPI startup. Safe to call multiple times.
    """
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=settings.MINIO_BUCKET)
    except ClientError:
        client.create_bucket(Bucket=settings.MINIO_BUCKET)


def upload_file(file_bytes: bytes, object_key: str, content_type: str = "application/pdf") -> str:
    """Upload a file to MinIO and return the object key."""
    client = get_s3_client()
    client.put_object(
        Bucket=settings.MINIO_BUCKET,
        Key=object_key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return object_key


def download_file(object_key: str) -> bytes:
    """Download a file from MinIO and return its bytes."""
    client = get_s3_client()
    response = client.get_object(
        Bucket=settings.MINIO_BUCKET,
        Key=object_key,
    )
    return response["Body"].read()


def delete_file(object_key: str) -> None:
    """Delete a file from MinIO."""
    client = get_s3_client()
    client.delete_object(
        Bucket=settings.MINIO_BUCKET,
        Key=object_key,
    )