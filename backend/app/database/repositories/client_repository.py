import uuid
from typing import Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database.models.client import Client, ClientGSTINProfile
from app.database.repositories.base_repository import BaseRepository

class ClientRepository(BaseRepository[Client]):
    def __init__(self, db: AsyncSession):
        super().__init__(Client, db)

    async def get_with_gstins(self, client_id: Any) -> Optional[Client]:
        norm_id = self._normalize_id(client_id)
        result = await self.db.execute(
            select(Client)
            .options(selectinload(Client.gstin_profiles))
            .where(Client.id == norm_id)
        )
        return result.scalars().first()

    async def list_by_organization(
        self,
        org_id: Any,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Client]:
        norm_org_id = self._normalize_id(org_id)
        query = select(Client).where(Client.organization_id == norm_org_id)
        if status:
            query = query.where(Client.status == status)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Client.business_name.ilike(search_term)) |
                (Client.primary_gstin.ilike(search_term)) |
                (Client.contact_name.ilike(search_term))
            )
        query = query.order_by(Client.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_by_organization(
        self,
        org_id: Any,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        norm_org_id = self._normalize_id(org_id)
        query = select(func.count(Client.id)).where(Client.organization_id == norm_org_id)
        if status:
            query = query.where(Client.status == status)
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Client.business_name.ilike(search_term)) |
                (Client.primary_gstin.ilike(search_term))
            )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_gstin(self, org_id: Any, gstin: str) -> Optional[Client]:
        norm_org_id = self._normalize_id(org_id)
        result = await self.db.execute(
            select(Client)
            .where(Client.organization_id == norm_org_id, Client.primary_gstin == gstin.upper().strip())
        )
        return result.scalars().first()
