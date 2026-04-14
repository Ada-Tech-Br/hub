import uuid
from sqlalchemy import Boolean, String, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.base import AuditMixin
import enum


class UserType(str, enum.Enum):
    internal = "internal"
    external = "external"


class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"


class AuthProvider(str, enum.Enum):
    google = "google"
    otp = "otp"


class User(AuditMixin, Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    type: Mapped[UserType] = mapped_column(
        SAEnum(UserType, name="user_type"), nullable=False, default=UserType.external
    )
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"), nullable=False, default=UserRole.user
    )
    auth_provider: Mapped[AuthProvider] = mapped_column(
        SAEnum(AuthProvider, name="auth_provider"), nullable=False, default=AuthProvider.otp
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # OTP fields
    otp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    otp_expires_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Google OAuth
    google_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
