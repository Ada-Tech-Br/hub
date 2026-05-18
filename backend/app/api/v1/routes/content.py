import uuid

from app.core.config import settings
from app.core.deps import AdminUser, CurrentUser, DBSession
from app.core.exceptions import ForbiddenError, ValidationError
from app.core.security import create_content_access_token, decode_content_access_token
from app.models.content import ContentType, FileType
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
from app.services import content_service, s3_service
from fastapi import APIRouter, File, Query, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse

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
    body = content_service.get_content_access(
        db, content_id, current_user_id=current_user.id
    )

    # For file content served through the proxy, issue a short-lived content access
    # cookie so the browser can load sub-resources (CSS/JS/images) without auth headers.
    if body.file_type is not None:
        token = create_content_access_token(
            user_id=current_user.id, content_id=content_id
        )
        cookie_name = f"cat_{content_id.hex[:8]}"
        resp = JSONResponse(content=body.model_dump(mode="json"))
        resp.set_cookie(
            cookie_name,
            token,
            max_age=settings.CLOUDFRONT_COOKIE_MAX_AGE,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
        )
        return resp

    return body


@router.get("/{content_id}/serve", include_in_schema=False)
async def serve_content_index(content_id: uuid.UUID, db: DBSession, request: Request):
    return await _serve_content(content_id, db, request, file_path="")


@router.get("/{content_id}/serve/{file_path:path}", include_in_schema=False)
async def serve_content_file(
    content_id: uuid.UUID, db: DBSession, request: Request, file_path: str
):
    return await _serve_content(content_id, db, request, file_path=file_path)


async def _serve_content(
    content_id: uuid.UUID, db: DBSession, request: Request, file_path: str
) -> StreamingResponse | RedirectResponse:
    """
    Proxy endpoint: verifies access then streams the requested file from S3.

    Private content requires the short-lived cookie set by GET /access.
    Public content is served to anyone without authentication.

    When no file_path is given, redirects to the actual index URL (e.g. /serve/index.html
    or /serve/dist/index.html) so the browser resolves relative asset imports
    (CSS, JS, images) against the correct base directory.
    """
    content = content_service.get_content_by_id(db, content_id)

    if not content.is_public:
        cookie_name = f"cat_{content_id.hex[:8]}"
        token = request.cookies.get(cookie_name)
        if not token:
            raise ForbiddenError("Content access token required. Call /access first.")
        payload = decode_content_access_token(token)
        if not payload or payload.get("cid") != str(content_id):
            raise ForbiddenError("Invalid or expired content access token")

    if not file_path:
        # Redirect to the explicit index path so that relative imports in the HTML
        # (e.g. <script src="./bundle.js">) resolve to /serve/bundle.js, not /bundle.js.
        if content.s3_path:
            if content.file_type == FileType.zip and content.uploaded_file_path:
                index_base = content.uploaded_file_path.rstrip("/")
            else:
                index_base = "/".join(content.s3_path.split("/")[:-1])
            relative_index = content.s3_path[len(index_base) + 1 :]
        else:
            relative_index = "index.html"

        base_path = request.url.path.rstrip("/")
        return RedirectResponse(url=f"{base_path}/{relative_index}", status_code=302)

    s3_key = content_service.resolve_serve_s3_key(db, content_id, file_path)
    body_iter, content_type, content_length = s3_service.stream_s3_object(s3_key)

    headers: dict[str, str] = {}
    if content_length is not None:
        headers["Content-Length"] = str(content_length)

    return StreamingResponse(body_iter, media_type=content_type, headers=headers)


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
