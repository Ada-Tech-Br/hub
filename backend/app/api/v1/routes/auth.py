from app.core.config import settings
from app.core.deps import CurrentUser, DBSession
from app.schemas.auth import OTPRequest, OTPVerify, RefreshTokenRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services import auth_service
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google")
def google_login():
    """Redirect to Google OAuth consent screen (fallback — prefer frontend-initiated flow)."""
    from urllib.parse import urlencode

    params = urlencode(
        {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "select_account",
        }
    )
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.get("/google/callback")
def google_callback(code: str, db: DBSession) -> TokenResponse:
    """Handle Google OAuth callback."""
    return auth_service.handle_google_callback(db, code)


@router.post("/otp/request")
def request_otp(data: OTPRequest, db: DBSession) -> dict:
    """Request OTP code via email."""
    return auth_service.request_otp(db, data)


@router.post("/otp/verify")
def verify_otp(data: OTPVerify, db: DBSession) -> TokenResponse:
    """Verify OTP code and return tokens."""
    return auth_service.verify_otp(db, data)


@router.post("/refresh")
def refresh_token(data: RefreshTokenRequest, db: DBSession) -> TokenResponse:
    """Refresh access token."""
    return auth_service.refresh_access_token(db, data.refresh_token)


@router.get("/me")
def get_me(current_user: CurrentUser) -> UserResponse:
    """Get current authenticated user."""
    return UserResponse.model_validate(current_user)
