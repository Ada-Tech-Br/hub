import uuid
from typing import Annotated

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import verify_token
from app.db.base import get_db
from app.models.user import User, UserRole
from app.services.user_service import get_user_by_id
from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(bearer_scheme)],
    db: Session = Depends(get_db),
) -> User:
    payload = verify_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedError()

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError()

    user = get_user_by_id(db, uuid.UUID(user_id))
    if not user.is_active:
        raise UnauthorizedError("Account is deactivated")

    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise ForbiddenError("Admin access required")
    return current_user


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(get_admin_user)]
DBSession = Annotated[Session, Depends(get_db)]
