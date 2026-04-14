from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request

from app.core.config import settings
from app.api.v1 import api_router

app = FastAPI(
    title="Ada Platform API",
    description="Hub digital de projetos e arquivos da Ada",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Backwards-compatible shorthand routes (without /api/v1 prefix)
from app.api.v1.routes import auth as auth_routes, users as user_routes, content as content_routes

app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(content_routes.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ada-platform"}
