import uuid
import random
import string
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.core.exceptions import UnauthorizedError, BadRequestError, NotFoundError
from app.models.user import User, UserType, UserRole, AuthProvider
from app.schemas.auth import TokenResponse, OTPRequest, OTPVerify
from app.schemas.user import UserResponse
from app.services.user_service import get_user_by_email


def _build_token_response(user: User) -> TokenResponse:
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


def generate_otp_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def request_otp(db: Session, data: OTPRequest) -> dict:
    user = get_user_by_email(db, data.email)
    if not user or not user.is_active:
        # Always return success to prevent email enumeration
        return {"message": "If your email is registered, you will receive a code."}

    if user.auth_provider != AuthProvider.otp:
        raise BadRequestError("This account uses a different authentication method")

    code = generate_otp_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    user.otp_secret = code
    user.otp_expires_at = expires_at.isoformat()
    db.commit()

    # Send email via Resend
    try:
        _send_otp_email(user.email, user.name, code)
    except Exception:
        pass  # Log but don't fail the request

    return {"message": "If your email is registered, you will receive a code."}


def _send_otp_email(email: str, name: str, code: str) -> None:
    if not settings.RESEND_API_KEY:
        return  # Skip in dev without API key

    import resend
    resend.api_key = settings.RESEND_API_KEY
    resend.Emails.send({
        "from": settings.EMAIL_FROM,
        "to": email,
        "subject": "Seu código de acesso - Ada",
        "html": f"""
        <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
          <h2>Olá, {name}!</h2>
          <p>Seu código de acesso é:</p>
          <div style="font-size: 36px; font-weight: bold; letter-spacing: 8px; 
                      text-align: center; padding: 24px; background: #f4f4f5; 
                      border-radius: 8px; margin: 24px 0;">
            {code}
          </div>
          <p>Este código expira em {settings.OTP_EXPIRE_MINUTES} minutos.</p>
          <p>Se você não solicitou este código, ignore este e-mail.</p>
        </div>
        """,
    })


def verify_otp(db: Session, data: OTPVerify) -> TokenResponse:
    user = get_user_by_email(db, data.email)
    if not user or not user.is_active:
        raise UnauthorizedError("Invalid credentials")

    if not user.otp_secret or not user.otp_expires_at:
        raise UnauthorizedError("No OTP requested for this account")

    expires_at = datetime.fromisoformat(user.otp_expires_at)
    if datetime.now(timezone.utc) > expires_at:
        raise UnauthorizedError("OTP code has expired")

    if user.otp_secret != data.code:
        raise UnauthorizedError("Invalid OTP code")

    # Clear OTP after successful verification
    user.otp_secret = None
    user.otp_expires_at = None
    db.commit()

    return _build_token_response(user)


def handle_google_callback(db: Session, code: str) -> TokenResponse:
    token_data = _exchange_google_code(code)
    user_info = _get_google_user_info(token_data["access_token"])

    email = user_info["email"]
    google_id = user_info["sub"]

    user = get_user_by_email(db, email)

    if not user:
        # Auto-create internal user on first Google login
        user = User(
            name=user_info.get("name", email.split("@")[0]),
            email=email,
            type=UserType.internal,
            role=UserRole.user,
            auth_provider=AuthProvider.google,
            google_id=google_id,
            avatar_url=user_info.get("picture"),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not user.is_active:
            raise UnauthorizedError("Account is deactivated")
        if user.auth_provider != AuthProvider.google:
            raise BadRequestError("This account uses a different authentication method")
        user.google_id = google_id
        user.avatar_url = user_info.get("picture")
        db.commit()

    return _build_token_response(user)


def _exchange_google_code(code: str) -> dict:
    response = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )
    if response.status_code != 200:
        raise UnauthorizedError("Google authentication failed")
    return response.json()


def _get_google_user_info(access_token: str) -> dict:
    response = httpx.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if response.status_code != 200:
        raise UnauthorizedError("Failed to get Google user info")
    return response.json()


def refresh_access_token(db: Session, refresh_token: str) -> TokenResponse:
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid refresh token")

    from app.services.user_service import get_user_by_id
    user = get_user_by_id(db, uuid.UUID(payload["sub"]))

    if not user.is_active:
        raise UnauthorizedError("Account is deactivated")

    return _build_token_response(user)
