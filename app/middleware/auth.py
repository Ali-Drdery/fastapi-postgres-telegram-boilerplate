"""
JWT-based authentication and Role-Based Access Control (RBAC).

Design note: FastAPI's dependency-injection system is the idiomatic and
most testable way to guard routes -- unlike a blanket ASGI `Middleware`,
dependencies can be applied selectively per-router or per-route, are fully
visible in the OpenAPI docs, and are trivial to override in tests
(`app.dependency_overrides[...]`). This module therefore exposes two
composable dependencies instead of a raw `BaseHTTPMiddleware`:

    get_current_user  -> validates the JWT and loads the user
    require_role(...) -> a dependency FACTORY for per-route RBAC
"""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decodes the bearer JWT, loads the corresponding active user, or raises 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception

    try:
        user_id = UUID(payload["sub"])
    except (ValueError, TypeError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory enforcing RBAC. Stack it on top of `get_current_user`.

    Usage:
        @router.get(
            "/admin-only",
            dependencies=[Depends(require_role(UserRole.ADMIN))],
        )
        async def admin_only(): ...

    Or, to also access the resolved user object in the endpoint body:
        async def admin_only(user: User = Depends(require_role(UserRole.ADMIN))):
            ...
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker
