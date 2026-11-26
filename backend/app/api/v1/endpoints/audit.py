from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models.user import User
from app.database.repositories.audit_repository import AuditRepository
from app.schemas.common import SuccessResponse, PaginatedResponse
from app.core.dependencies import get_current_user

router = APIRouter()

@router.get("", response_model=PaginatedResponse[Dict[str, Any]])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = AuditRepository(db)
    skip = (page - 1) * page_size
    logs = await repo.list_logs(
        organization_id=str(current_user.organization_id),
        action=action,
        resource_type=resource_type,
        skip=skip,
        limit=page_size
    )
    total = await repo.count_logs(
        organization_id=str(current_user.organization_id),
        action=action,
        resource_type=resource_type
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    log_data = []
    for l in logs:
        log_data.append({
            "id": str(l.id),
            "created_at": l.created_at.isoformat() if l.created_at else None,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "details": l.details,
            "user_email": l.user.email if l.user else "system"
        })

    return PaginatedResponse(
        success=True,
        data=log_data,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
