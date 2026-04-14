import io
import os
import uuid
import zipfile
import tempfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.exceptions import BadRequestError, ValidationError


def _get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def upload_html_file(content_id: uuid.UUID, file_content: bytes, filename: str) -> str:
    """Upload a single HTML file to S3 and return its path."""
    s3 = _get_s3_client()
    s3_key = f"content/{content_id}/{filename}"

    s3.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=s3_key,
        Body=file_content,
        ContentType="text/html",
    )
    return s3_key


def upload_zip_content(content_id: uuid.UUID, zip_bytes: bytes) -> str:
    """
    Validates ZIP contains index.html, extracts and uploads all files to S3.
    Returns the base S3 path.
    """
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()

        # Validate index.html exists (at root or one level deep)
        has_index = any(
            name == "index.html" or name.endswith("/index.html")
            for name in names
        )
        if not has_index:
            raise ValidationError("ZIP file must contain an index.html file")

        s3 = _get_s3_client()
        base_path = f"content/{content_id}"

        for name in names:
            if name.endswith("/"):
                continue  # Skip directories

            file_data = zf.read(name)
            content_type = _guess_content_type(name)
            s3_key = f"{base_path}/{name}"

            s3.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=s3_key,
                Body=file_data,
                ContentType=content_type,
            )

    return base_path


def get_presigned_url(s3_path: str, expiration: int = 3600) -> str:
    """Generate a presigned URL for private S3 object."""
    s3 = _get_s3_client()
    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": s3_path},
            ExpiresIn=expiration,
        )
        return url
    except ClientError as e:
        raise BadRequestError(f"Failed to generate access URL: {str(e)}")


def get_public_url(s3_path: str) -> str:
    """Return the public URL for an S3 object."""
    base = settings.S3_PUBLIC_URL or f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com"
    return f"{base}/{s3_path}"


def _guess_content_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    mapping = {
        ".html": "text/html",
        ".htm": "text/html",
        ".css": "text/css",
        ".js": "application/javascript",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".ttf": "font/ttf",
        ".mp4": "video/mp4",
        ".webp": "image/webp",
    }
    return mapping.get(ext, "application/octet-stream")
