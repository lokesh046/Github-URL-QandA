# utils/s3_store.py

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from config import (
    R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY,
    R2_BUCKET_NAME,
    S3_ENDPOINT_URL,
    S3_STORAGE_ENABLED
)

# Initialize S3 client if storage is enabled
s3_client = None
if S3_STORAGE_ENABLED:
    s3_client = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4")
    )


def s3_exists(key: str) -> bool:
    """Check if an object exists in the S3 bucket."""
    if not S3_STORAGE_ENABLED:
        return False
    try:
        s3_client.head_object(Bucket=R2_BUCKET_NAME, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise RuntimeError(f"Failed to check S3 file existence: {e}")


def s3_upload(data: bytes, key: str):
    """Upload raw bytes to the S3 bucket."""
    if not S3_STORAGE_ENABLED:
        return
    try:
        s3_client.put_object(Bucket=R2_BUCKET_NAME, Key=key, Body=data)
        print(f"[S3 Storage] Uploaded file: {key} ({len(data)} bytes)")
    except Exception as e:
        raise RuntimeError(f"Failed to upload to S3: {e}")


def s3_download(key: str) -> bytes:
    """Download an object from the S3 bucket as bytes."""
    if not S3_STORAGE_ENABLED:
        raise RuntimeError("S3 storage is not enabled.")
    try:
        response = s3_client.get_object(Bucket=R2_BUCKET_NAME, Key=key)
        return response["Body"].read()
    except Exception as e:
        raise RuntimeError(f"Failed to download from S3: {e}")


def s3_delete(key: str):
    """Delete an object from the S3 bucket."""
    if not S3_STORAGE_ENABLED:
        return
    try:
        s3_client.delete_object(Bucket=R2_BUCKET_NAME, Key=key)
        print(f"[S3 Storage] Deleted file: {key}")
    except Exception as e:
        print(f"Warning: Failed to delete {key} from S3: {e}")
