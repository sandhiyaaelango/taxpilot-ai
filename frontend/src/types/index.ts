export interface User {
  id: string
  email: string
  full_name: string
  role: 'AUDITOR' | 'ADMIN'
  organization_id: string
  is_active: boolean
  created_at: string
}

export interface Organization {
  id: string
  name: string
  plan: string
  created_at: string
}

export interface Client {
  id: string
  organization_id: string
  business_name: string
  primary_gstin: string
  contact_name: string
  contact_email: string
  contact_phone?: string
  state_code: string
  industry?: string
  status: 'ACTIVE' | 'INACTIVE'
  created_at: string
  updated_at: string
  gstins?: ClientGSTIN[]
}

export interface ClientGSTIN {
  id: string
  client_id: string
  gstin: string
  trade_name?: string
  registration_type?: string
  state_code?: string
  is_primary: boolean
}

export type InvestigationStatus =
  | 'PENDING'
  | 'PARSING_NOTICE'
  | 'VALIDATING_NOTICE'
  | 'BUILDING_PLAN'
  | 'INVESTIGATING'
  | 'CHALLENGING_EVIDENCE'
  | 'VERIFYING'
  | 'DRAFTING_RESPONSE'
  | 'AWAITING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'NEEDS_MORE_EVIDENCE'
  | 'COMPLETED'
  | 'FAILED'

export interface Investigation {
  id: string
  client_id: string
  organization_id: string
  title: string
  status: InvestigationStatus
  notice_id?: string
  workflow_state?: Record<string, unknown>
  mismatch_amount?: number
  tax_period?: string
  response_deadline?: string
  created_at: string
  updated_at: string
  client?: Client
  notice?: Notice
}

export interface Notice {
  id: string
  investigation_id: string
  notice_number: string
  notice_type: string
  gstin: string
  tax_period: string
  itc_claimed: number
  itc_available: number
  itc_mismatch: number
  response_deadline?: string
  raw_text?: string
  extraction_confidence?: number
  status: 'PENDING' | 'PARSED' | 'VALIDATED' | 'INVALID'
  created_at: string
}

export type EvidenceStatus = 'SUPPORTED' | 'CONTRADICTED' | 'UNVERIFIED' | 'PENDING'
export type HypothesisType =
  | 'TIMING_DIFFERENCE'
  | 'DUPLICATE_INVOICE'
  | 'SUPPLIER_FILING_ISSUE'
  | 'MISSING_ACCOUNTING_ENTRY'
  | 'INCORRECT_AMOUNT'
  | 'INCORRECT_TAX_PERIOD'

export interface Hypothesis {
  id: string
  investigation_id: string
  hypothesis_type: HypothesisType
  title: string
  description: string
  status: EvidenceStatus
  confidence_score?: number
  supporting_evidence_count: number
  contradicting_evidence_count: number
  created_at: string
}

export interface EvidenceRecord {
  id: string
  investigation_id: string
  source_id: string
  source_type: 'INVOICE' | 'LEDGER_ENTRY' | 'GST_RETURN' | 'SUPPLIER_FILING' | 'NOTICE'
  document_name: string
  amount?: number
  tax_period?: string
  gstin?: string
  status: EvidenceStatus
  retrieved_at: string
  verification_notes?: string
}

export interface AgentRun {
  id: string
  investigation_id: string
  agent_name: string
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'
  started_at?: string
  completed_at?: string
  input_tokens?: number
  output_tokens?: number
  estimated_cost_usd?: number
  error_message?: string
  tool_calls?: ToolCall[]
}

export interface ToolCall {
  id: string
  agent_run_id: string
  tool_name: string
  mcp_server?: string
  arguments?: Record<string, unknown>
  result_status: 'SUCCESS' | 'ERROR' | 'TIMEOUT'
  duration_ms?: number
  retry_count: number
  called_at: string
}

export interface Approval {
  id: string
  investigation_id: string
  reviewer_id: string
  action: 'APPROVE' | 'EDIT' | 'REJECT' | 'REQUEST_MORE_EVIDENCE'
  notes?: string
  created_at: string
  reviewer?: User
}

export interface Report {
  id: string
  investigation_id: string
  report_type: 'INVESTIGATION' | 'RESPONSE_DRAFT' | 'FINAL'
  title: string
  content?: Record<string, unknown>
  pdf_path?: string
  created_at: string
}

export interface AuditLog {
  id: string
  user_id?: string
  organization_id?: string
  action: string
  resource_type: string
  resource_id?: string
  details?: Record<string, unknown>
  ip_address?: string
  created_at: string
  user?: User
}

export interface DashboardStats {
  total_investigations: number
  active_investigations: number
  pending_approvals: number
  completed_this_month: number
  total_clients: number
  notices_resolved: number
  avg_resolution_days: number
  total_itc_at_risk: number
}

export interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  success: boolean
  data: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ApiError {
  success: false
  error: {
    code: string
    message: string
    field?: string
  }
}
