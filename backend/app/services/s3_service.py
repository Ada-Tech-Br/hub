import base64
import datetime
import io
import json
import uuid
import zipfile
from pathlib import Path

import boto3
from app.core.config import settings
from app.core.exceptions import ValidationError
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def _normalize_zip_entry(name: str) -> str:
    return name.replace("\\", "/").strip("/")


def _find_index_zip_entry(names: list[str]) -> str:
    """Pick the ZIP member path for index.html (prefers root, else shallowest)."""
    files = [n for n in names if not n.endswith("/")]
    candidates: list[str] = []
    for n in files:
        norm = _normalize_zip_entry(n)
        if norm == "index.html" or norm.endswith("/index.html"):
            candidates.append(n)
    if not candidates:
        raise ValidationError("ZIP file must contain an index.html file")
    for c in candidates:
        if _normalize_zip_entry(c) == "index.html":
            return c
    return min(candidates, key=lambda x: _normalize_zip_entry(x).count("/"))


def _get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def _content_prefix(content_id: uuid.UUID, is_public: bool) -> str:
    tier = "public" if is_public else "private"
    return f"{tier}/content/{content_id}"


def upload_html_file(
    content_id: uuid.UUID, file_content: bytes, filename: str, is_public: bool
) -> str:
    """Upload a single HTML file to S3 and return its key."""
    s3 = _get_s3_client()
    s3_key = f"{_content_prefix(content_id, is_public)}/{filename}"

    s3.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=s3_key,
        Body=file_content,
        ContentType="text/html",
    )
    return s3_key


def upload_zip_content(
    content_id: uuid.UUID, zip_bytes: bytes, is_public: bool
) -> tuple[str, str]:
    """
    Validates ZIP contains index.html, extracts and uploads all files to S3.
    Returns (base_prefix, index_object_key).
    Files land under public/content/{id}/... or private/content/{id}/...
    """
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        index_entry = _find_index_zip_entry(names)

        s3 = _get_s3_client()
        base_path = _content_prefix(content_id, is_public)

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

        index_s3_key = f"{base_path}/{index_entry}"
    return base_path, index_s3_key


def get_signed_url(s3_path: str, expiration: int = 3600) -> str:
    """Gera CloudFront Signed URL para conteúdo privado."""
    cf_domain = settings.CLOUDFRONT_DOMAIN
    key_id = settings.CLOUDFRONT_KEY_ID
    private_key_pem = settings.CLOUDFRONT_PRIVATE_KEY
    url = f"https://{cf_domain}/{s3_path}"
    expire_time = int(
        (
            datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration)
        ).timestamp()
    )
    policy = json.dumps(
        {
            "Statement": [
                {
                    "Resource": url,
                    "Condition": {"DateLessThan": {"AWS:EpochTime": expire_time}},
                }
            ]
        },
        separators=(",", ":"),
    )
    private_key = serialization.load_pem_private_key(
        private_key_pem.replace("\\n", "\n").encode(), password=None
    )
    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise ValidationError("CloudFront signing key must be an RSA PEM private key")
    signature = private_key.sign(policy.encode(), padding.PKCS1v15(), hashes.SHA1())

    def _cf_b64(data: bytes) -> str:
        return (
            base64.b64encode(data)
            .decode()
            .replace("+", "-")
            .replace("=", "_")
            .replace("/", "~")
        )

    return (
        f"{url}"
        f"?Policy={_cf_b64(policy.encode())}"
        f"&Signature={_cf_b64(signature)}"
        f"&Key-Pair-Id={key_id}"
    )


def get_public_url(s3_path: str) -> str:
    """Return the permanent CloudFront URL for a public object."""
    return f"https://{settings.CLOUDFRONT_DOMAIN}/{s3_path}"


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
