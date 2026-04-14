from pydantic import BaseModel, EmailStr
from app.schemas.user import UserResponse


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    code: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
