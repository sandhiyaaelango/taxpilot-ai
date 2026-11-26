from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models.user import User
from app.database.models.organization import Organization, OrganizationMember
from app.database.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email.lower().strip()))
        return result.scalars().first()

    async def get_by_organization(self, org_id: str, skip: int = 0, limit: int = 50) -> List[User]:
        result = await self.db.execute(
            select(User)
            .where(User.organization_id == org_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
