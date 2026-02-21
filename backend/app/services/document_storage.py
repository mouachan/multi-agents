"""
Document storage service — S3/MinIO with local filesystem fallback.

When S3_ENDPOINT_URL is configured, documents are read from MinIO.
Otherwise, falls back to local filesystem (Docker volumes / OpenShift PVC).
"""

import io
import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Lazy-initialized S3 client
_s3_client = None


def _get_s3_client():
    """Get or create the S3 client (singleton)."""
    global _s3_client
    if _s3_client is None and settings.s3_enabled:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
        )
        logger.info(f"S3 client initialized: {settings.s3_endpoint_url}")
    return _s3_client


def _bucket_for_entity(entity_type: str) -> str:
    """Return the S3 bucket name for a given entity type."""
    if entity_type == "tender":
        return settings.s3_bucket_tenders
    return settings.s3_bucket_claims


def _s3_key_from_path(stored_path: str) -> str:
    """Extract S3 object key from a stored document_path.

    Stored paths look like:
      /mnt/documents/claims/CLM-2024-0001.pdf
      /mnt/documents/tenders/AO-2025-IDF-001.pdf
      /claim_documents/ao/AO-2025-IDF-002.pdf

    We extract just the filename as the S3 key (flat bucket structure).
    """
    return os.path.basename(stored_path)


def _resolve_local_path(stored_path: str) -> Optional[str]:
    """Resolve document path on local filesystem.

    Stored paths are relative: 'claims/file.pdf' or 'tenders/file.pdf'.
    Docker mounts ./documents:/documents, so we look under /documents/.
    """
    candidates = [
        # Direct: /documents/claims/file.pdf
        os.path.join("/documents", stored_path.lstrip("/")),
        # Absolute path as-is
        stored_path,
    ]

    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def get_document(stored_path: str, entity_type: str = "claim") -> Optional[tuple[bytes, str]]:
    """Fetch a document by its stored path.

    Returns (file_bytes, filename) or None if not found.
    Tries S3 first (if configured), then local filesystem.
    """
    filename = os.path.basename(stored_path)

    # Try S3 first
    s3 = _get_s3_client()
    if s3:
        bucket = _bucket_for_entity(entity_type)
        key = _s3_key_from_path(stored_path)
        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            data = response["Body"].read()
            logger.info(f"Document served from S3: s3://{bucket}/{key} ({len(data)} bytes)")
            return data, filename
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchKey":
                logger.debug(f"Document not in S3 bucket '{bucket}': {key}")
            else:
                logger.warning(f"S3 error for {key}: {e}")
        except (NoCredentialsError, Exception) as e:
            logger.warning(f"S3 access error: {e}")

    # Fallback to local filesystem
    local_path = _resolve_local_path(stored_path)
    if local_path:
        with open(local_path, "rb") as f:
            data = f.read()
        logger.info(f"Document served from filesystem: {local_path} ({len(data)} bytes)")
        return data, filename

    return None


def upload_document(file_data: bytes, filename: str, entity_type: str = "claim") -> Optional[str]:
    """Upload a document to S3. Returns the S3 key or None if S3 is not configured."""
    s3 = _get_s3_client()
    if not s3:
        return None

    bucket = _bucket_for_entity(entity_type)
    key = filename

    try:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=file_data,
            ContentType="application/pdf",
        )
        logger.info(f"Document uploaded to S3: s3://{bucket}/{key} ({len(file_data)} bytes)")
        return key
    except (ClientError, NoCredentialsError) as e:
        logger.error(f"Failed to upload to S3: {e}")
        return None


def list_documents(entity_type: str = "claim", prefix: str = "") -> list[str]:
    """List document keys in an S3 bucket. Returns empty list if S3 is not configured."""
    s3 = _get_s3_client()
    if not s3:
        return []

    bucket = _bucket_for_entity(entity_type)
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        return [obj["Key"] for obj in response.get("Contents", [])]
    except (ClientError, NoCredentialsError) as e:
        logger.error(f"Failed to list S3 objects: {e}")
        return []
