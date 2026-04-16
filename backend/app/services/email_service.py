"""Transactional email via Amazon SES."""

from typing import Any

import boto3

from app.core.config import settings


def _ses_client() -> Any:
    kwargs: dict[str, str] = {"region_name": settings.ses_region}
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    return boto3.client("ses", **kwargs)


def send_html_email(
    *,
    to_addresses: list[str],
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> None:
    """
    Send one email through SES. ``EMAIL_FROM`` must be a verified identity in SES.
    Raises ``ClientError`` on API failure.
    """
    body: dict[str, dict[str, str]] = {
        "Html": {"Charset": "UTF-8", "Data": html_body},
    }
    if text_body:
        body["Text"] = {"Charset": "UTF-8", "Data": text_body}

    client = _ses_client()
    client.send_email(
        Source=settings.EMAIL_FROM,
        Destination={"ToAddresses": to_addresses},
        Message={
            "Subject": {"Charset": "UTF-8", "Data": subject},
            "Body": body,
        },
    )
