import logging
import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.content import AccessMode, Content, ContentAccess, ContentType, FileType
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.content import (
    AccessControlResponse,
    AccessControlUser,
    ContentAccessResponse,
    ContentCreate,
    ContentUpdate,
    SnippetResponse,
)
from app.services import s3_service
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

logger = logging.getLogger("app.services.content_service")


def get_content_by_id(db: Session, content_id: uuid.UUID) -> Content:
    content = db.scalar(
        select(Content).where(Content.id == content_id, Content.is_deleted == False)
    )
    if not content:
        raise NotFoundError("Content not found")
    return content


def list_contents(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    type: ContentType | None = None,
    is_public: bool | None = None,
) -> PaginatedResponse:
    query = select(Content).where(Content.is_deleted == False)

    if search:
        query = query.where(Content.title.ilike(f"%{search}%"))
    if type:
        query = query.where(Content.type == type)
    if is_public is not None:
        query = query.where(Content.is_public == is_public)

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = db.scalars(
        query.order_by(Content.created_at.desc())
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


def create_content(
    db: Session, data: ContentCreate, created_by: uuid.UUID | None = None
) -> Content:
    content = Content(
        title=data.title,
        description=data.description,
        type=data.type,
        icon=data.icon,
        is_public=data.is_public,
        external_url=data.external_url,
        file_type=data.file_type,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    return content


def update_content(
    db: Session,
    content_id: uuid.UUID,
    data: ContentUpdate,
    updated_by: uuid.UUID | None = None,
) -> Content:
    content = get_content_by_id(db, content_id)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(content, field, value)

    content.updated_by = updated_by
    content.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(content)
    return content


def soft_delete_content(
    db: Session, content_id: uuid.UUID, deleted_by: uuid.UUID | None = None
) -> None:
    content = get_content_by_id(db, content_id)
    content.is_deleted = True
    content.deleted_at = datetime.now(timezone.utc)
    content.deleted_by = deleted_by
    db.commit()


def handle_html_upload(
    db: Session,
    content_id: uuid.UUID,
    file_bytes: bytes,
    filename: str,
    updated_by: uuid.UUID | None = None,
) -> Content:
    content = get_content_by_id(db, content_id)
    if content.type != ContentType.file:
        raise ValidationError("Content must be of type 'file'")

    s3_key = s3_service.upload_html_file(
        content_id, file_bytes, filename, is_public=content.is_public
    )
    content.s3_path = s3_key
    content.file_type = FileType.html
    content.uploaded_file_path = filename
    content.updated_by = updated_by
    content.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(content)
    return content


def handle_zip_upload(
    db: Session,
    content_id: uuid.UUID,
    zip_bytes: bytes,
    updated_by: uuid.UUID | None = None,
) -> Content:
    content = get_content_by_id(db, content_id)
    if content.type != ContentType.file:
        raise ValidationError("Content must be of type 'file'")

    base_path, index_s3_key = s3_service.upload_zip_content(
        content_id, zip_bytes, is_public=content.is_public
    )
    content.s3_path = index_s3_key
    content.file_type = FileType.zip
    content.uploaded_file_path = base_path
    content.updated_by = updated_by
    content.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(content)
    return content


def _check_user_access(db: Session, content: Content, user_id: uuid.UUID) -> bool:
    """Returns True if the user is allowed to access private content."""
    if content.access_mode == AccessMode.all_users:
        return True
    grant = db.scalar(
        select(ContentAccess).where(
            ContentAccess.content_id == content.id,
            ContentAccess.user_id == user_id,
        )
    )
    return grant is not None


def get_content_access(
    db: Session, content_id: uuid.UUID, current_user_id: uuid.UUID
) -> ContentAccessResponse:
    content = get_content_by_id(db, content_id)

    if content.type == ContentType.project:
        return ContentAccessResponse(
            access_url=content.external_url or "",
            type=content.type,
        )

    if not content.s3_path:
        raise ValidationError("Content has no associated file")

    if not content.is_public and not _check_user_access(db, content, current_user_id):
        logger.info(
            "content_access_denied content_id=%s user_id=%s access_mode=%s",
            content_id,
            current_user_id,
            content.access_mode.value,
        )
        raise ForbiddenError("You do not have access to this content")

    if content.is_public:
        access_url = s3_service.get_public_url(content.s3_path)
    else:
        access_url = s3_service.get_signed_url(content.s3_path)

    return ContentAccessResponse(
        access_url=access_url,
        type=content.type,
        file_type=content.file_type,
    )


def get_access_control(db: Session, content_id: uuid.UUID) -> AccessControlResponse:
    content = get_content_by_id(db, content_id)
    users: list[AccessControlUser] = []
    if content.access_mode == AccessMode.specific_users:
        rows = db.scalars(
            select(User)
            .join(ContentAccess, ContentAccess.user_id == User.id)
            .where(
                ContentAccess.content_id == content_id,
                User.is_deleted == False,
            )
            .order_by(User.name)
        ).all()
        users = [AccessControlUser.model_validate(u) for u in rows]
    return AccessControlResponse(access_mode=content.access_mode, users=users)


def set_access_mode(
    db: Session,
    content_id: uuid.UUID,
    mode: AccessMode,
    updated_by: uuid.UUID | None = None,
) -> AccessControlResponse:
    content = get_content_by_id(db, content_id)
    content.access_mode = mode
    content.updated_by = updated_by
    content.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(content)
    return get_access_control(db, content_id)


def grant_users(
    db: Session,
    content_id: uuid.UUID,
    user_ids: list[uuid.UUID],
    granted_by: uuid.UUID | None = None,
) -> AccessControlResponse:
    get_content_by_id(db, content_id)
    existing = set(
        db.scalars(
            select(ContentAccess.user_id).where(ContentAccess.content_id == content_id)
        ).all()
    )
    new_grants = [
        ContentAccess(content_id=content_id, user_id=uid, granted_by=granted_by)
        for uid in user_ids
        if uid not in existing
    ]
    if new_grants:
        db.add_all(new_grants)
        db.commit()
    return get_access_control(db, content_id)


def revoke_user(db: Session, content_id: uuid.UUID, user_id: uuid.UUID) -> None:
    db.execute(
        delete(ContentAccess).where(
            ContentAccess.content_id == content_id,
            ContentAccess.user_id == user_id,
        )
    )
    db.commit()


def generate_snippet(db: Session, content_id: uuid.UUID) -> SnippetResponse:
    content = get_content_by_id(db, content_id)

    if content.type != ContentType.project or content.is_public:
        raise ValidationError("Snippets are only available for private projects")

    snippet = f"""<!-- Ada Platform - Access Control Snippet -->
<script>
(function() {{
  var ADA_API = "{settings.FRONTEND_URL}";
  var CONTENT_ID = "{content_id}";

  function getCookie(name) {{
    var matches = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/([\\.$?*|{{}}\\(\\)\\[\\]\\\\\\/\\+\\^])/g, '\\\\$1') + '=([^;]*)'));
    return matches ? decodeURIComponent(matches[1]) : undefined;
  }}

  function getToken() {{
    return localStorage.getItem('ada_access_token') || getCookie('ada_access_token');
  }}

  function redirectToLogin() {{
    window.location.href = ADA_API + '/login?redirect=' + encodeURIComponent(window.location.href);
  }}

  async function validateAccess() {{
    var token = getToken();
    if (!token) {{
      redirectToLogin();
      return;
    }}

    try {{
      var response = await fetch(ADA_API.replace(':5173', ':8000') + '/content/{content_id}/access', {{
        method: 'GET',
        headers: {{
          'Authorization': 'Bearer ' + token,
          'Content-Type': 'application/json'
        }}
      }});

      if (response.status === 401 || response.status === 403) {{
        redirectToLogin();
        return;
      }}

      if (!response.ok) {{
        document.body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif"><p>Access error. Please try again.</p></div>';
        return;
      }}
    }} catch (e) {{
      redirectToLogin();
    }}
  }}

  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', validateAccess);
  }} else {{
    validateAccess();
  }}
}})();
</script>"""

    return SnippetResponse(content_id=content_id, snippet=snippet)
