import logging
from contextlib import asynccontextmanager

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

setup_logging()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup env=%s log_level=%s", settings.APP_ENV, settings.LOG_LEVEL)
    yield


app = FastAPI(
    title="Ada Platform API",
    description="Hub digital de projetos e arquivos da Ada",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)


@app.exception_handler(HTTPException)
async def http_exception_with_logging(request: Request, exc: HTTPException):
    if exc.status_code >= 500:
        logger.error(
            "http_error status=%s method=%s path=%s detail=%s",
            exc.status_code,
            request.method,
            request.url.path,
            exc.detail,
        )
    elif exc.status_code in (401, 403):
        logger.info(
            "http_error status=%s method=%s path=%s detail=%s",
            exc.status_code,
            request.method,
            request.url.path,
            exc.detail,
        )
    else:
        logger.debug(
            "http_error status=%s method=%s path=%s detail=%s",
            exc.status_code,
            request.method,
            request.url.path,
            exc.detail,
        )
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_with_logging(
    request: Request, exc: RequestValidationError
):
    logger.warning(
        "validation_error method=%s path=%s errors=%s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger.exception(
        "unhandled_error method=%s path=%s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(api_router)

# Backwards-compatible shorthand routes (without /api/v1 prefix)
from app.api.v1.routes import auth as auth_routes
from app.api.v1.routes import content as content_routes
from app.api.v1.routes import users as user_routes

app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(content_routes.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ada-platform"}
