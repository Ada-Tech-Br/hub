import uuid

from app.core.deps import AdminUser, CurrentUser, DBSession
from app.core.exceptions import ValidationError
from app.models.content import ContentType
from app.schemas.common import PaginatedResponse
from app.schemas.content import (
    AccessControlResponse,
    ContentAccessResponse,
    ContentCreate,
    ContentListResponse,
    ContentResponse,
    ContentUpdate,
    GrantUsersRequest,
    SetAccessModeRequest,
    SnippetResponse,
)
from app.services import content_service
from fastapi import APIRouter, File, Query, UploadFile

router = APIRouter(prefix="/content", tags=["content"])

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB


@router.get("", response_model=PaginatedResponse[ContentListResponse])
def list_contents(
    db: DBSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    type: ContentType | None = Query(default=None),
):
    result = content_service.list_contents(
        db, page=page, page_size=page_size, search=search, type=type
    )
    return PaginatedResponse[ContentListResponse](
        items=[ContentListResponse.model_validate(c) for c in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.post("", response_model=ContentResponse, status_code=201)
def create_content(data: ContentCreate, db: DBSession, admin: AdminUser):
    content = content_service.create_content(db, data, created_by=admin.id)
    return ContentResponse.model_validate(content)


@router.get("/{content_id}", response_model=ContentResponse)
def get_content(content_id: uuid.UUID, db: DBSession, current_user: CurrentUser):
    return ContentResponse.model_validate(
        content_service.get_content_by_id(db, content_id)
    )


@router.patch("/{content_id}", response_model=ContentResponse)
def update_content(
    content_id: uuid.UUID, data: ContentUpdate, db: DBSession, admin: AdminUser
):
    content = content_service.update_content(db, content_id, data, updated_by=admin.id)
    return ContentResponse.model_validate(content)


@router.delete("/{content_id}", status_code=204)
def delete_content(content_id: uuid.UUID, db: DBSession, admin: AdminUser):
    content_service.soft_delete_content(db, content_id, deleted_by=admin.id)


@router.post("/upload", response_model=ContentResponse)
async def upload_file(
    db: DBSession,
    admin: AdminUser,
    content_id: uuid.UUID = Query(...),
    file: UploadFile = File(...),
):
    file_bytes = await file.read()

    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise ValidationError("File exceeds maximum size of 50MB")

    filename = file.filename or "upload"

    if filename.endswith(".zip"):
        content = content_service.handle_zip_upload(
            db, content_id, file_bytes, updated_by=admin.id
        )
    elif filename.endswith(".html") or filename.endswith(".htm"):
        content = content_service.handle_html_upload(
            db, content_id, file_bytes, filename, updated_by=admin.id
        )
    else:
        raise ValidationError("Only .html and .zip files are supported")

    return ContentResponse.model_validate(content)


@router.get("/{content_id}/access", response_model=ContentAccessResponse)
def get_content_access(content_id: uuid.UUID, db: DBSession, current_user: CurrentUser):
    return content_service.get_content_access(
        db, content_id, current_user_id=current_user.id
    )


@router.get("/{content_id}/snippet", response_model=SnippetResponse)
def get_snippet(content_id: uuid.UUID, db: DBSession, admin: AdminUser):
    return content_service.generate_snippet(db, content_id)


@router.get("/{content_id}/access-control", response_model=AccessControlResponse)
def get_access_control(content_id: uuid.UUID, db: DBSession, admin: AdminUser):
    return content_service.get_access_control(db, content_id)


@router.patch("/{content_id}/access-control", response_model=AccessControlResponse)
def set_access_mode(
    content_id: uuid.UUID, data: SetAccessModeRequest, db: DBSession, admin: AdminUser
):
    return content_service.set_access_mode(
        db, content_id, data.access_mode, updated_by=admin.id
    )


@router.post("/{content_id}/access-control/users", response_model=AccessControlResponse)
def grant_users(
    content_id: uuid.UUID, data: GrantUsersRequest, db: DBSession, admin: AdminUser
):
    return content_service.grant_users(
        db, content_id, data.user_ids, granted_by=admin.id
    )


@router.delete("/{content_id}/access-control/users/{user_id}", status_code=204)
def revoke_user(
    content_id: uuid.UUID, user_id: uuid.UUID, db: DBSession, admin: AdminUser
):
    content_service.revoke_user(db, content_id, user_id)
