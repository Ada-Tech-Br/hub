import uuid
from datetime import datetime

from app.models.content import AccessMode, ContentType, FileType
from pydantic import BaseModel, model_validator


class ContentBase(BaseModel):
    title: str
    description: str | None = None
    type: ContentType
    icon: str | None = None
    is_public: bool = True


class ContentCreate(ContentBase):
    external_url: str | None = None
    file_type: FileType | None = None

    @model_validator(mode="after")
    def validate_content(self) -> "ContentCreate":
        if self.type == ContentType.project and not self.external_url:
            raise ValueError("external_url is required for project type")
        return self


class ContentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    icon: str | None = None
    is_public: bool | None = None
    external_url: str | None = None


class ContentResponse(ContentBase):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    external_url: str | None = None
    file_type: FileType | None = None
    s3_path: str | None = None
    uploaded_file_path: str | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class ContentListResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    description: str | None = None
    type: ContentType
    icon: str | None = None
    is_public: bool
    external_url: str | None = None
    file_type: FileType | None = None
    s3_path: str | None = None
    created_at: datetime


class ContentAccessResponse(BaseModel):
    access_url: str
    type: ContentType
    file_type: FileType | None = None


class SnippetResponse(BaseModel):
    content_id: uuid.UUID
    snippet: str


class AccessControlUser(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    email: str
    avatar_url: str | None = None


class AccessControlResponse(BaseModel):
    access_mode: AccessMode
    users: list[AccessControlUser]


class SetAccessModeRequest(BaseModel):
    access_mode: AccessMode


class GrantUsersRequest(BaseModel):
    user_ids: list[uuid.UUID]
