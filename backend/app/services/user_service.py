import uuid
from datetime import datetime, timezone

from app.core.exceptions import ConflictError, NotFoundError
from app.models.user import User, UserRole, UserType
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserUpdate
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User:
    user = db.scalar(select(User).where(User.id == user_id, User.is_deleted == False))
    if not user:
        raise NotFoundError("User not found")
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email, User.is_deleted == False))


def list_users(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    role: UserRole | None = None,
    type: UserType | None = None,
    is_active: bool | None = None,
) -> PaginatedResponse:
    query = select(User).where(User.is_deleted == False)

    if search:
        query = query.where(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
        )
    if role:
        query = query.where(User.role == role)
    if type:
        query = query.where(User.type == type)
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = db.scalars(
        query.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return PaginatedResponse(
        items=list(items),
        total=total or 0,
        page=page,
        page_size=page_size,
        total_pages=max(1, -(-(total or 0) // page_size)),
    )


def create_user(
    db: Session, data: UserCreate, created_by: uuid.UUID | None = None
) -> User:
    existing = get_user_by_email(db, data.email)
    if existing:
        raise ConflictError("Email already registered")

    user = User(
        name=data.name,
        email=data.email,
        type=data.type,
        role=data.role,
        auth_provider=data.auth_provider,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user_id: uuid.UUID,
    data: UserUpdate,
    updated_by: uuid.UUID | None = None,
) -> User:
    user = get_user_by_id(db, user_id)

    if data.email and data.email != user.email:
        existing = get_user_by_email(db, data.email)
        if existing:
            raise ConflictError("Email already registered")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)

    user.updated_by = updated_by
    user.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(user)
    return user


def soft_delete_user(
    db: Session, user_id: uuid.UUID, deleted_by: uuid.UUID | None = None
) -> None:
    user = get_user_by_id(db, user_id)
    user.is_deleted = True
    user.deleted_at = datetime.now(timezone.utc)
    user.deleted_by = deleted_by
    user.is_active = False
    db.commit()


def toggle_user_active(
    db: Session,
    user_id: uuid.UUID,
    is_active: bool,
    updated_by: uuid.UUID | None = None,
) -> User:
    user = get_user_by_id(db, user_id)
    user.is_active = is_active
    user.updated_by = updated_by
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user
