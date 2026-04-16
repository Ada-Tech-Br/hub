from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
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
    # If empty, ``AWS_REGION`` is used (e.g. SES in another region than S3).
    SES_REGION: str = ""
    S3_BUCKET_NAME: str = "ada-platform-files"

    CLOUDFRONT_DOMAIN: str = ""
    CLOUDFRONT_KEY_ID: str = ""
    CLOUDFRONT_PRIVATE_KEY: str = ""

    EMAIL_FROM: str = "noreply@ada.tech"

    FRONTEND_URL: str = "http://localhost:5173"

    OTP_EXPIRE_MINUTES: int = 10

    @property
    def ses_region(self) -> str:
        return self.SES_REGION or self.AWS_REGION


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
