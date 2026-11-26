from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

class ApprovalRequest(BaseModel):
    action: str  # APPROVE / EDIT / REJECT / REQUEST_MORE_EVIDENCE
    notes: Optional[str] = None
    edited_content: Optional[Dict[str, Any]] = None

class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    reviewer_id: str
    action: str
    notes: Optional[str] = None
    is_final: bool
    created_at: Optional[datetime] = None

class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    report_type: str
    title: str
    content: Optional[Dict[str, Any]] = None
    pdf_path: Optional[str] = None
    is_latest: bool
    generated_by: Optional[str] = None
    created_at: Optional[datetime] = None
