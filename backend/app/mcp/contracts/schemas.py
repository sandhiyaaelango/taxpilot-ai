from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal

# --- TAX PORTAL MCP CONTRACTS ---

class GetNoticeInput(BaseModel):
    notice_id: str = Field(..., description="Notice number or internal notice ID (e.g., ZA271223001928K)")

class NoticeDetailOutput(BaseModel):
    source_id: str
    notice_number: str
    notice_type: str
    gstin: str
    tax_period: str
    itc_claimed: float
    itc_available: float
    itc_mismatch: float
    response_deadline: str
    issued_date: str
    issuing_authority: str
    discrepancy_details: List[Dict[str, Any]]
    retrieved_at: str

class GetFiledReturnsInput(BaseModel):
    gstin: str = Field(..., description="15-character GSTIN")
    tax_period: str = Field(..., description="Tax period in YYYY-MM format")

class FiledReturnSummary(BaseModel):
    source_id: str
    return_type: str
    tax_period: str
    arn: str
    filing_date: str
    status: str
    total_taxable_value: float
    itc_eligible: float

class GetFiledReturnsOutput(BaseModel):
    source_id: str
    gstin: str
    tax_period: str
    returns: List[FiledReturnSummary]
    retrieved_at: str

class GetReturnDetailsInput(BaseModel):
    gstin: str
    return_type: str = Field(..., description="GSTR-1, GSTR-2B, or GSTR-3B")
    tax_period: str = Field(..., description="YYYY-MM format")

class ReturnLineItem(BaseModel):
    source_id: str
    invoice_number: str
    supplier_gstin: str
    invoice_date: str
    taxable_value: float
    cgst: float
    sgst: float
    igst: float
    total_tax: float
    filing_date: Optional[str] = None

class GetReturnDetailsOutput(BaseModel):
    source_id: str
    gstin: str
    return_type: str
    tax_period: str
    line_items: List[ReturnLineItem]
    retrieved_at: str

class GetVendorFilingStatusInput(BaseModel):
    supplier_gstin: str = Field(..., description="Supplier's 15-character GSTIN")
    tax_period: str = Field(..., description="YYYY-MM format")

class GetVendorFilingStatusOutput(BaseModel):
    source_id: str
    supplier_gstin: str
    supplier_name: str
    tax_period: str
    gstr1_status: str  # FILED / NOT_FILED
    gstr1_filing_date: Optional[str] = None
    gstr1_arn: Optional[str] = None
    gstr3b_status: str  # FILED / NOT_FILED
    gstr3b_filing_date: Optional[str] = None
    invoices_reported: int
    total_invoice_value: float
    retrieved_at: str

# --- LEDGER MCP CONTRACTS ---

class GetEntriesByPeriodInput(BaseModel):
    gstin: str = Field(..., description="Client GSTIN")
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")

class LedgerRecord(BaseModel):
    source_id: str
    entry_date: str
    tax_period: str
    account_code: str
    account_name: str
    narration: str
    debit_amount: float
    credit_amount: float
    invoice_reference: Optional[str] = None

class GetEntriesByPeriodOutput(BaseModel):
    source_id: str
    gstin: str
    start_date: str
    end_date: str
    total_debits: float
    total_credits: float
    entries: List[LedgerRecord]
    retrieved_at: str

class GetInvoiceDetailsInput(BaseModel):
    invoice_id: str = Field(..., description="Invoice number or UUID")

class InvoiceDetailOutput(BaseModel):
    source_id: str
    invoice_number: str
    supplier_gstin: str
    supplier_name: str
    buyer_gstin: str
    invoice_date: str
    tax_period: str
    taxable_amount: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    total_tax: float
    invoice_value: float
    payment_status: str
    po_number: Optional[str] = None
    e_way_bill_no: Optional[str] = None
    retrieved_at: str

class SearchInvoicesInput(BaseModel):
    supplier_gstin: Optional[str] = None
    tax_period: Optional[str] = None
    amount: Optional[float] = None
    amount_tolerance: Optional[float] = 100.0  # INR tolerance for partial matches

class SearchInvoicesOutput(BaseModel):
    source_id: str
    query_params: Dict[str, Any]
    total_matches: int
    matches: List[InvoiceDetailOutput]
    retrieved_at: str

class GetLedgerRecordsInput(BaseModel):
    invoice_id: str
    gstin: Optional[str] = None
    period: Optional[str] = None

class GetLedgerRecordsOutput(BaseModel):
    source_id: str
    invoice_id: str
    reconciliation_status: str  # RECONCILED / UNMATCHED / PARTIAL
    entries: List[LedgerRecord]
    total_claimed_in_ledger: float
    retrieved_at: str
