from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.config.security import decode_access_token
from app.config.logging import get_logger

logger = get_logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    from app.database.repositories.user_repository import UserRepository
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

async def get_current_active_user(current_user = Depends(get_current_user)):
    return current_user

def normalize_role(role: str | None) -> str:
    """Normalize legacy or current role strings into the strict two-role model: AUDITOR or ADMIN."""
    r = (role or "").upper().strip()
    if r in {"ADMIN", "OWNER"}:
        return "ADMIN"
    return "AUDITOR"


class RequireRole:
    def __init__(self, *roles: str):
        self.roles = {normalize_role(r) for r in roles}
    
    def __call__(self, current_user = Depends(get_current_user)):
        user_role = normalize_role(current_user.role)
        if user_role not in self.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions for this action. Required role: {', '.join(sorted(self.roles))}, your role: {user_role}."
            )
        return current_user

require_admin = RequireRole("ADMIN")
require_owner = require_admin
# Auditor is responsible for investigations, editing responses, and approving responses
require_auditor = RequireRole("AUDITOR")
# Note: Admin is for management/monitoring, not for auto-approving investigations
require_accountant = require_auditor
require_any = RequireRole("AUDITOR", "ADMIN")
