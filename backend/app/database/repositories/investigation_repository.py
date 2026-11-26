from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database.models.investigation import Investigation
from app.database.models.notice import Notice, UploadedDocument
from app.database.models.agent import AgentRun, ToolCall
from app.database.repositories.base_repository import BaseRepository

class InvestigationRepository(BaseRepository[Investigation]):
    def __init__(self, db: AsyncSession):
        super().__init__(Investigation, db)

    async def get_with_details(self, investigation_id: str) -> Optional[Investigation]:
        clean_id = self._normalize_id(investigation_id)
        result = await self.db.execute(
            select(Investigation)
            .options(
                selectinload(Investigation.notice),
                selectinload(Investigation.client),
                selectinload(Investigation.documents),
                selectinload(Investigation.agent_runs).selectinload(AgentRun.tool_calls),
                selectinload(Investigation.hypotheses),
                selectinload(Investigation.evidence_records),
                selectinload(Investigation.approvals),
                selectinload(Investigation.reports)
            )
            .where(Investigation.id == clean_id)
        )
        return result.scalars().first()

    async def list_by_organization(
        self,
        org_id: str,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        client_id: Optional[str] = None
    ) -> List[Investigation]:
        norm_org_id = self._normalize_id(org_id)
        query = select(Investigation).options(
            selectinload(Investigation.client),
            selectinload(Investigation.notice)
        ).where(Investigation.organization_id == norm_org_id)

        if status:
            query = query.where(Investigation.status == status)
        if client_id:
            query = query.where(Investigation.client_id == self._normalize_id(client_id))

        query = query.order_by(Investigation.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_by_organization(
        self,
        org_id: str,
        status: Optional[str] = None,
        client_id: Optional[str] = None
    ) -> int:
        norm_org_id = self._normalize_id(org_id)
        query = select(func.count(Investigation.id)).where(Investigation.organization_id == norm_org_id)
        if status:
            query = query.where(Investigation.status == status)
        if client_id:
            query = query.where(Investigation.client_id == self._normalize_id(client_id))
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_idempotency_key(self, key: str) -> Optional[Investigation]:
        result = await self.db.execute(select(Investigation).where(Investigation.idempotency_key == key))
        return result.scalars().first()
