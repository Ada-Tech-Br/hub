import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from app.models.user import UserType, UserRole, AuthProvider


class UserBase(BaseModel):
    name: str
    email: EmailStr
    type: UserType = UserType.external
    role: UserRole = UserRole.user
    auth_provider: AuthProvider = AuthProvider.otp


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    type: UserType | None = None
    role: UserRole | None = None
    auth_provider: AuthProvider | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    is_active: bool
    avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    email: str
    type: UserType
    role: UserRole
    auth_provider: AuthProvider
    is_active: bool
    avatar_url: str | None = None
    created_at: datetime
