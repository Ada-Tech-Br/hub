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
from starlette.responses import Response


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


def _cf_url_safe_b64(data: bytes) -> str:
    return (
        base64.b64encode(data).decode().replace("+", "-").replace("=", "_").replace("/", "~")
    )


def _load_cloudfront_private_key() -> rsa.RSAPrivateKey:
    pem = settings.CLOUDFRONT_PRIVATE_KEY.replace("\\n", "\n").encode()
    key = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(key, rsa.RSAPrivateKey):
        raise ValidationError("CloudFront signing key must be an RSA PEM private key")
    return key


def _resolve_cloudfront_cookie_domain() -> str:
    explicit = (settings.CLOUDFRONT_COOKIE_DOMAIN or "").strip()
    if explicit:
        return explicit if explicit.startswith(".") else f".{explicit}"
    host = settings.CLOUDFRONT_DOMAIN.strip().lower().split("/")[0].split(":")[0]
    if not host or host.endswith(".cloudfront.net"):
        return ""
    parts = host.split(".")
    if len(parts) < 3:
        return ""
    return "." + ".".join(parts[1:])


def _cloudfront_cookie_path(s3_path: str) -> str:
    parts = s3_path.split("/")
    if len(parts) >= 3 and parts[0] == "private" and parts[1] == "content":
        return "/" + "/".join(parts[:3]) + "/"
    return "/"


def _cloudfront_wildcard_resource_url(s3_path: str) -> str:
    cf_domain = settings.CLOUDFRONT_DOMAIN.strip().lower().split("/")[0].split(":")[0]
    parts = s3_path.split("/")
    if len(parts) >= 3 and parts[0] == "private" and parts[1] == "content":
        prefix = "/".join(parts[:3])
        return f"https://{cf_domain}/{prefix}/*"
    return f"https://{cf_domain}/{s3_path}"


def _cloudfront_sign_policy_for_resource(resource: str, max_age: int) -> tuple[str, str, str]:
    expire_time = int(
        (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=max_age)).timestamp()
    )
    policy_bytes = json.dumps(
        {
            "Statement": [
                {
                    "Resource": resource,
                    "Condition": {"DateLessThan": {"AWS:EpochTime": expire_time}},
                }
            ]
        },
        separators=(",", ":"),
    ).encode()
    private_key = _load_cloudfront_private_key()
    signature = private_key.sign(policy_bytes, padding.PKCS1v15(), hashes.SHA1())
    return (
        _cf_url_safe_b64(policy_bytes),
        _cf_url_safe_b64(signature),
        settings.CLOUDFRONT_KEY_ID,
    )


def attach_cloudfront_signed_cookies(
    response: Response,
    s3_path: str,
    expiration: int | None = None,
) -> None:
    """
    Set CloudFront signed cookies so the browser can load all objects under the
    private content prefix (HTML, CSS, JS) without a signed query string on each URL.
    """
    max_age = expiration if expiration is not None else settings.CLOUDFRONT_COOKIE_MAX_AGE
    domain = _resolve_cloudfront_cookie_domain()
    if not domain:
        raise ValidationError(
            "Configure CLOUDFRONT_COOKIE_DOMAIN (e.g. .stg.ada.tech) so signed cookies "
            "apply to your CDN hostname. Cannot infer a safe parent domain for "
            "*.cloudfront.net."
        )

    resource = _cloudfront_wildcard_resource_url(s3_path)
    policy_b64, signature_b64, key_id = _cloudfront_sign_policy_for_resource(resource, max_age)
    path = _cloudfront_cookie_path(s3_path)

    cookie_kwargs = {
        "domain": domain,
        "path": path,
        "max_age": max_age,
        "secure": True,
        "httponly": True,
        "samesite": "none",
    }
    response.set_cookie("CloudFront-Policy", policy_b64, **cookie_kwargs)
    response.set_cookie("CloudFront-Signature", signature_b64, **cookie_kwargs)
    response.set_cookie("CloudFront-Key-Pair-Id", key_id, **cookie_kwargs)


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
