from fastapi import APIRouter, Depends

from app.middleware.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    """Any authenticated user can read their own profile."""
    return current_user


@router.get("/admin-area", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def admin_only_endpoint() -> dict:
    """Example route restricted to the ADMIN role via the RBAC dependency."""
    return {"message": "Welcome, admin. This route is protected by RBAC."}
