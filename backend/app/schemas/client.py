from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
import re

GSTIN_REGEX = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"

class GSTINProfileCreate(BaseModel):
    gstin: str
    trade_name: Optional[str] = None
    registration_type: Optional[str] = "Regular"
    state_code: Optional[str] = None
    is_primary: bool = False

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: str) -> str:
        clean = v.strip().upper()
        if not re.match(GSTIN_REGEX, clean):
            raise ValueError(f"Invalid GSTIN format: {clean}")
        return clean

class GSTINProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_id: str
    gstin: str
    trade_name: Optional[str] = None
    registration_type: Optional[str] = None
    state_code: Optional[str] = None
    is_primary: bool
    is_active: bool

class ClientCreate(BaseModel):
    business_name: str = Field(..., min_length=2)
    primary_gstin: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    state_code: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None

    @field_validator("primary_gstin")
    @classmethod
    def validate_primary_gstin(cls, v: str) -> str:
        clean = v.strip().upper()
        if not re.match(GSTIN_REGEX, clean):
            raise ValueError(f"Invalid GSTIN format: {clean}")
        return clean

class ClientUpdate(BaseModel):
    business_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    state_code: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None

class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    business_name: str
    primary_gstin: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    state_code: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None
    status: str
    is_demo: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    gstin_profiles: Optional[List[GSTINProfileResponse]] = []
