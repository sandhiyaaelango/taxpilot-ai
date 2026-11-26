from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.database.models.user import User
from app.database.models.agent import BackgroundJob
from app.schemas.common import SuccessResponse
from app.core.dependencies import get_current_user

router = APIRouter()

@router.get("", response_model=SuccessResponse[List[Dict[str, Any]]])
async def list_background_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = await db.execute(
        select(BackgroundJob).order_by(BackgroundJob.created_at.desc()).limit(20)
    )
    jobs = query.scalars().all()
    return SuccessResponse(
        data=[
            {
                "id": str(j.id),
                "job_type": j.job_type,
                "status": j.status,
                "retry_count": j.retry_count,
                "created_at": j.created_at.isoformat() if j.created_at else None
            }
            for j in jobs
        ]
    )
