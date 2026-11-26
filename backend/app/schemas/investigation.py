from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from app.schemas.agent import AgentRunResponse

class NoticeCreate(BaseModel):
    notice_number: Optional[str] = None
    notice_type: Optional[str] = "DRC-01A"
    gstin: Optional[str] = None
    tax_period: Optional[str] = None
    itc_claimed: Optional[Decimal] = None
    itc_available: Optional[Decimal] = None
    itc_mismatch: Optional[Decimal] = None
    response_deadline: Optional[date] = None
    issued_date: Optional[date] = None
    issuing_authority: Optional[str] = None
    raw_text: Optional[str] = None

class NoticeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    notice_number: Optional[str] = None
    notice_type: Optional[str] = None
    gstin: Optional[str] = None
    tax_period: Optional[str] = None
    itc_claimed: Optional[float] = None
    itc_available: Optional[float] = None
    itc_mismatch: Optional[float] = None
    response_deadline: Optional[date] = None
    issued_date: Optional[date] = None
    issuing_authority: Optional[str] = None
    extraction_confidence: Optional[float] = None
    status: str

class NoticeUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    investigation_id: str
    filename: str
    file_size_bytes: int
    is_scanned: bool
    ocr_required: bool
    notice: NoticeResponse
    validation_status: str
    warnings: List[str] = []

class InvestigationCreate(BaseModel):
    client_id: str
    title: str
    description: Optional[str] = None
    tax_period: Optional[str] = None
    mismatch_amount: Optional[Decimal] = None
    response_deadline: Optional[date] = None
    idempotency_key: Optional[str] = None

class InvestigationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    response_deadline: Optional[date] = None

class InvestigationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    client_id: str
    title: str
    description: Optional[str] = None
    status: str
    mismatch_amount: Optional[float] = None
    tax_period: Optional[str] = None
    response_deadline: Optional[date] = None
    days_remaining: Optional[int] = None
    is_overdue: Optional[bool] = None
    deadline_urgency: Optional[str] = None
    is_demo: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    client_business_name: Optional[str] = None
    client_gstin: Optional[str] = None
    notice: Optional[NoticeResponse] = None
    workflow_state: Optional[Dict[str, Any]] = None
    agent_runs: Optional[List[AgentRunResponse]] = None
