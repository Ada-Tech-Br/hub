import enum
import uuid
from datetime import datetime, timezone

from app.db.base import Base
from app.models.base import AuditMixin
from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ContentType(str, enum.Enum):
    project = "project"
    file = "file"


class FileType(str, enum.Enum):
    html = "html"
    zip = "zip"
    external = "external"


class AccessMode(str, enum.Enum):
    all_users = "all_users"
    specific_users = "specific_users"


class Content(AuditMixin, Base):
    __tablename__ = "contents"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[ContentType] = mapped_column(
        SAEnum(ContentType, name="content_type"), nullable=False
    )
    icon: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    access_mode: Mapped[AccessMode] = mapped_column(
        SAEnum(AccessMode, name="access_mode"),
        nullable=False,
        default=AccessMode.all_users,
    )

    # For project type
    external_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # For file type
    file_type: Mapped[FileType | None] = mapped_column(
        SAEnum(FileType, name="file_type"), nullable=True
    )
    s3_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    uploaded_file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    access_grants: Mapped[list["ContentAccess"]] = relationship(
        "ContentAccess", back_populates="content", cascade="all, delete-orphan"
    )


class ContentAccess(Base):
    __tablename__ = "content_access"

    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    content: Mapped["Content"] = relationship("Content", back_populates="access_grants")
