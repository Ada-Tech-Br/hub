import uuid

from app.core.deps import AdminUser, DBSession
from app.models.user import UserRole, UserType
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services import user_service
from fastapi import APIRouter, Query

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=PaginatedResponse[UserListResponse])
def list_users(
    db: DBSession,
    _admin: AdminUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    role: UserRole | None = Query(default=None),
    type: UserType | None = Query(default=None),
    is_active: bool | None = Query(default=None),
):
    result = user_service.list_users(
        db,
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        type=type,
        is_active=is_active,
    )
    return PaginatedResponse[UserListResponse](
        items=[UserListResponse.model_validate(u) for u in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.post("", response_model=UserResponse, status_code=201)
def create_user(data: UserCreate, db: DBSession, admin: AdminUser):
    user = user_service.create_user(db, data, created_by=admin.id)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, db: DBSession, _admin: AdminUser):
    user = user_service.get_user_by_id(db, user_id)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: uuid.UUID, data: UserUpdate, db: DBSession, admin: AdminUser):
    user = user_service.update_user(db, user_id, data, updated_by=admin.id)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: uuid.UUID, db: DBSession, admin: AdminUser):
    user_service.soft_delete_user(db, user_id, deleted_by=admin.id)


@router.patch("/{user_id}/activate", response_model=UserResponse)
def activate_user(user_id: uuid.UUID, db: DBSession, admin: AdminUser):
    user = user_service.toggle_user_active(
        db, user_id, is_active=True, updated_by=admin.id
    )
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(user_id: uuid.UUID, db: DBSession, admin: AdminUser):
    user = user_service.toggle_user_active(
        db, user_id, is_active=False, updated_by=admin.id
    )
    return UserResponse.model_validate(user)
