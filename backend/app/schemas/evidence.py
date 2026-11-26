from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class EvidenceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    source_id: str
    source_type: str
    document_name: Optional[str] = None
    amount: Optional[float] = None
    tax_period: Optional[str] = None
    gstin: Optional[str] = None
    retrieved_at: Optional[datetime] = None
    retrieved_by: Optional[str] = None
    mcp_server: Optional[str] = None
    status: str
    verification_notes: Optional[str] = None

class HypothesisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    hypothesis_type: str
    title: str
    description: Optional[str] = None
    status: str
    confidence_score: Optional[float] = None
    supporting_evidence_count: int
    contradicting_evidence_count: int
    missing_evidence_description: Optional[str] = None
    investigator_rationale: Optional[str] = None
    challenge_rationale: Optional[str] = None
    created_at: Optional[datetime] = None
    evidence_records: Optional[List[EvidenceRecordResponse]] = []

class EvidenceAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    hypothesis_id: str
    assessed_by: str
    assessment_type: str
    result: str
    rationale: Optional[str] = None
    evidence_gaps: Optional[str] = None
