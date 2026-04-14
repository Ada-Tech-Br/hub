from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    DATABASE_URL: str = "postgresql://ada:ada@localhost:5432/ada_platform"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    # Path relativo ao FRONTEND_URL, ex: /auth/google/callback
    GOOGLE_REDIRECT_PATH: str = "/auth/google/callback"

    @property
    def GOOGLE_REDIRECT_URI(self) -> str:
        return f"{self.FRONTEND_URL}{self.GOOGLE_REDIRECT_PATH}"

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "ada-platform-files"
    S3_PUBLIC_URL: str = ""

    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@ada.com.br"

    FRONTEND_URL: str = "http://localhost:5173"

    OTP_EXPIRE_MINUTES: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
