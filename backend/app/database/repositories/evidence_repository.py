import uuid
from typing import Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database.models.evidence import Hypothesis, EvidenceRecord, EvidenceLink, EvidenceAssessment
from app.database.repositories.base_repository import BaseRepository

class EvidenceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _normalize_id(self, id_val: Any) -> Any:
        if isinstance(id_val, str):
            try:
                return uuid.UUID(id_val)
            except ValueError:
                return id_val
        return id_val

    async def get_hypotheses(self, investigation_id: str) -> List[Hypothesis]:
        norm_id = self._normalize_id(investigation_id)
        result = await self.db.execute(
            select(Hypothesis)
            .options(
                selectinload(Hypothesis.evidence_records),
                selectinload(Hypothesis.assessments)
            )
            .where(Hypothesis.investigation_id == norm_id)
            .order_by(Hypothesis.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_evidence_records(self, investigation_id: str) -> List[EvidenceRecord]:
        norm_id = self._normalize_id(investigation_id)
        result = await self.db.execute(
            select(EvidenceRecord)
            .where(EvidenceRecord.investigation_id == norm_id)
            .order_by(EvidenceRecord.retrieved_at.desc())
        )
        return list(result.scalars().all())

    async def create_hypothesis(self, **kwargs) -> Hypothesis:
        hyp = Hypothesis(**kwargs)
        self.db.add(hyp)
        await self.db.flush()
        await self.db.refresh(hyp)
        return hyp

    async def create_evidence_record(self, **kwargs) -> EvidenceRecord:
        record = EvidenceRecord(**kwargs)
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def link_evidence_to_hypothesis(
        self,
        hypothesis_id: str,
        evidence_record_id: str,
        relationship_type: str,
        relationship_reason: Optional[str] = None
    ) -> EvidenceLink:
        link = EvidenceLink(
            hypothesis_id=hypothesis_id,
            evidence_record_id=evidence_record_id,
            relationship_type=relationship_type,
            relationship_reason=relationship_reason
        )
        self.db.add(link)
        await self.db.flush()
        return link

    async def add_assessment(self, **kwargs) -> EvidenceAssessment:
        assessment = EvidenceAssessment(**kwargs)
        self.db.add(assessment)
        await self.db.flush()
        await self.db.refresh(assessment)
        return assessment
