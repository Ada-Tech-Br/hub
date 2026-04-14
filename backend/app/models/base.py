import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditMixin:
    """Common audit fields for all entities."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
