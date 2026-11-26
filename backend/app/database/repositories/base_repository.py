import uuid
from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    def _normalize_id(self, id_val: Any) -> Any:
        if isinstance(id_val, str):
            try:
                return uuid.UUID(id_val)
            except ValueError:
                return id_val
        return id_val

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        norm_id = self._normalize_id(id)
        result = await self.db.execute(select(self.model).where(self.model.id == norm_id))
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        result = await self.db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(self.model.id)))
        return result.scalar_one()

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: Any, **kwargs) -> Optional[ModelType]:
        norm_id = self._normalize_id(id)
        await self.db.execute(
            update(self.model).where(self.model.id == norm_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_by_id(norm_id)

    async def delete(self, id: Any) -> bool:
        norm_id = self._normalize_id(id)
        result = await self.db.execute(delete(self.model).where(self.model.id == norm_id))
        await self.db.flush()
        return result.rowcount > 0
