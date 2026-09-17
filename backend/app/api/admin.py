from fastapi import APIRouter, Depends

from app.core.deps import require_role
from app.models.enums import UserRole
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping")
async def admin_ping(current_user: User = Depends(require_role(UserRole.staff_admin))) -> dict:
    return {"status": "ok", "user": current_user.email}
