import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database.models.audit import AuditLog, UsageMetric

class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _normalize_id(self, id_val: Any) -> Any:
        if isinstance(id_val, str):
            try:
                return uuid.UUID(id_val)
            except ValueError:
                return id_val
        return id_val

    async def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        log = AuditLog(
            created_at=datetime.now(timezone.utc),
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            user_id=self._normalize_id(user_id) if user_id else None,
            organization_id=self._normalize_id(organization_id) if organization_id else None,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def list_logs(
        self,
        organization_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[AuditLog]:
        query = select(AuditLog).options(selectinload(AuditLog.user))
        if organization_id:
            query = query.where(AuditLog.organization_id == self._normalize_id(organization_id))
        if action:
            query = query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)

        query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_logs(
        self,
        organization_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None
    ) -> int:
        query = select(func.count(AuditLog.id))
        if organization_id:
            query = query.where(AuditLog.organization_id == self._normalize_id(organization_id))
        if action:
            query = query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def record_usage_metric(self, **kwargs) -> UsageMetric:
        metric = UsageMetric(
            created_at=datetime.now(timezone.utc),
            **kwargs
        )
        self.db.add(metric)
        await self.db.flush()
        return metric
