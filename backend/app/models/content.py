import uuid
import enum
from sqlalchemy import String, Text, Boolean, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.base import AuditMixin


class ContentType(str, enum.Enum):
    project = "project"
    file = "file"


class FileType(str, enum.Enum):
    html = "html"
    zip = "zip"
    external = "external"


class Content(AuditMixin, Base):
    __tablename__ = "contents"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[ContentType] = mapped_column(
        SAEnum(ContentType, name="content_type"), nullable=False
    )
    icon: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # For project type
    external_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # For file type
    file_type: Mapped[FileType | None] = mapped_column(
        SAEnum(FileType, name="file_type"), nullable=True
    )
    s3_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    uploaded_file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
