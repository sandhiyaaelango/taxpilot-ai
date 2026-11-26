import uuid
from typing import Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database.models.approval import Approval, Report

class ApprovalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _normalize_id(self, id_val: Any) -> Any:
        if isinstance(id_val, str):
            try:
                return uuid.UUID(id_val)
            except ValueError:
                return id_val
        return id_val

    async def get_by_investigation(self, investigation_id: str) -> List[Approval]:
        norm_id = self._normalize_id(investigation_id)
        result = await self.db.execute(
            select(Approval)
            .options(selectinload(Approval.reviewer))
            .where(Approval.investigation_id == norm_id)
            .order_by(Approval.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_approval(self, **kwargs) -> Approval:
        approval = Approval(**kwargs)
        self.db.add(approval)
        await self.db.flush()
        await self.db.refresh(approval)
        return approval

    async def get_report_by_id(self, report_id: str) -> Optional[Report]:
        norm_id = self._normalize_id(report_id)
        result = await self.db.execute(
            select(Report).where(Report.id == norm_id)
        )
        return result.scalars().first()

    async def get_report_by_investigation(self, investigation_id: str) -> Optional[Report]:
        norm_id = self._normalize_id(investigation_id)
        result = await self.db.execute(
            select(Report)
            .where(Report.investigation_id == norm_id, Report.is_latest == True)
            .order_by(Report.created_at.desc())
        )
        return result.scalars().first()

    async def create_report(self, **kwargs) -> Report:
        report = Report(**kwargs)
        self.db.add(report)
        await self.db.flush()
        await self.db.refresh(report)
        return report
