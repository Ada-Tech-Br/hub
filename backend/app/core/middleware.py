import logging
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        client = request.client.host if request.client else "-"
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request_failed method=%s path=%s client=%s duration_ms=%.1f",
                request.method,
                request.url.path,
                client,
                duration_ms,
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        log_fn = logger.debug if request.url.path == "/health" else logger.info
        log_fn(
            "method=%s path=%s status=%s client=%s duration_ms=%.1f",
            request.method,
            request.url.path,
            response.status_code,
            client,
            duration_ms,
        )
        return response
