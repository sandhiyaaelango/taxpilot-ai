# TaxPilot AI — Architecture Document

**Version:** 1.0  
**Date:** 2026-11-22  
**Classification:** Internal Technical Reference

---

## 1. System Overview

TaxPilot AI is an Agentic AI-Powered GST Notice Investigation & Evidence Intelligence Platform.  
It enables accountants and CA firms to investigate Indian GST Input Tax Credit (ITC) mismatch notices using a Supervisor–Worker multi-agent architecture, MCP servers, LangGraph orchestration, and human-in-the-loop approval.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         REACT FRONTEND (Vite + TypeScript)          │
│  Dashboard │ Clients │ Investigations │ Evidence │ Approvals │ Audit │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTPS / REST / SSE
┌──────────────────────────▼──────────────────────────────────────────┐
│                    FASTAPI BACKEND  (Python)                        │
│  Auth │ Clients │ Investigations │ Evidence │ Approvals │ Reports   │
│  ─────────────────────────────────────────────────────────────────  │
│                   LANGGRAPH WORKFLOW ORCHESTRATOR                   │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────────────────┐  │
│  │ Supervisor │→ │ Notice Parser│→ │   Ledger Matcher (ReAct)  │  │
│  │   Agent    │  │    Agent     │  └──────────────┬────────────┘  │
│  └────────────┘  └──────────────┘                 │               │
│         │                           ┌─────────────▼─────────────┐  │
│         │                           │ Root-Cause Investigator   │  │
│         │                           │       (ReAct)             │  │
│         │                           └─────────────┬─────────────┘  │
│         │                                         │               │
│         │                           ┌─────────────▼─────────────┐  │
│         │                           │ Evidence Challenge Engine │  │
│         │                           │       (ReAct)             │  │
│         │                           └─────────────┬─────────────┘  │
│         │                                         │               │
│         │                           ┌─────────────▼─────────────┐  │
│         │                           │   Verification Gate       │  │
│         │                           │  (Deterministic Python)   │  │
│         │                           └─────────────┬─────────────┘  │
│         │                                         │               │
│         │                           ┌─────────────▼─────────────┐  │
│         └─────────────────────────→ │   Response Drafter Agent  │  │
│                                     └─────────────┬─────────────┘  │
│                                                   │               │
│                                     ┌─────────────▼─────────────┐  │
│                                     │  Human Approval Gate      │  │
│                                     │  (Accountant Review)      │  │
│                                     └───────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ MCP Protocol
       ┌───────────────────┼──────────────────┐
       │                   │                  │
┌──────▼──────┐    ┌───────▼──────┐    ┌──────▼──────┐
│  TAX PORTAL │    │    LEDGER    │    │  PostgreSQL  │
│  MCP SERVER │    │  MCP SERVER  │    │  (Primary DB)│
│ (FastMCP)   │    │  (FastMCP)   │    │  + Alembic   │
└─────────────┘    └──────────────┘    └─────────────┘
       │                   │
  Mock GST Data      Mock Ledger Data
  (GSTR-2B, 3B)     (Invoices, Entries)
```

---

## 3. Monorepo Structure

```
taxpilot-ai/
├── frontend/          # React + TypeScript + Vite + Tailwind
├── backend/           # Python + FastAPI + LangGraph + SQLAlchemy
├── sample_documents/  # Demo notices, invoices, reports
├── scripts/           # Setup, seed, verification scripts
├── docs/              # Architecture, API, MCP, agent docs
├── .env.example
├── README.md
├── ARCHITECTURE.md
└── DEVELOPMENT_STATUS.md
```

---

## 4. Technology Stack

### Frontend
| Layer | Technology |
|-------|-----------|
| Framework | React 18 + TypeScript |
| Build Tool | Vite 5 |
| Styling | Tailwind CSS 3 |
| Routing | React Router 6 |
| HTTP Client | Axios |
| Server State | TanStack Query v5 |
| Forms | React Hook Form + Zod |
| Icons | Lucide React |
| Charts | Recharts |

### Backend
| Layer | Technology |
|-------|-----------|
| Framework | FastAPI + Pydantic v2 |
| ORM | SQLAlchemy 2 |
| Migrations | Alembic |
| Database | PostgreSQL 15 |
| Auth | JWT (python-jose) + bcrypt |
| Async | asyncio |

### Agentic AI
| Layer | Technology |
|-------|-----------|
| LLM Provider | Google Gemini API |
| SDK | google-genai (official) |
| Orchestration | LangGraph |
| MCP Servers | FastMCP |
| Observability | Langfuse |

### Document Processing
| Layer | Technology |
|-------|-----------|
| PDF Extraction | PyMuPDF (fitz) |
| OCR | pytesseract / google-cloud-vision fallback |
| Images | Pillow |

---

## 5. Agent Architecture

### 5.1 Supervisor Agent
- Receives investigation trigger
- Builds execution plan from notice data
- Delegates to worker agents via LangGraph edges
- Manages workflow state
- Triggers approval gate

### 5.2 Notice Parser Agent
- PDF/image text extraction with PyMuPDF
- OCR fallback for scanned documents
- Structured Pydantic extraction of GSTIN, notice number, ITC amounts, deadlines
- Never invents missing values — uses null + uncertainty flag

### 5.3 Ledger Matcher Agent (ReAct)
- 8-iteration bounded ReAct loop
- Tools: search_invoices, get_ledger_records (via Ledger MCP Server)
- Compares GSTIN, invoice numbers, amounts, periods
- Detects partial matches, duplicates, missing records

### 5.4 Root-Cause Investigator (ReAct)
- 8-iteration bounded ReAct loop
- Generates competing hypotheses (timing, duplicate, supplier issue, missing entry, amount error, period error)
- Calls both MCP servers for evidence per hypothesis
- Updates hypothesis status based on evidence

### 5.5 Evidence Challenge Engine (ReAct)
- Independent verification pass — does NOT repeat root-cause output
- 8-iteration bounded ReAct loop
- Independently identifies verification requirements per hypothesis
- Retrieves additional supporting AND contradictory evidence
- Classifies: SUPPORTED / CONTRADICTED / UNVERIFIED
- Records provenance for every evidence item

### 5.6 Response Drafter Agent
- Reads only SUPPORTED findings from verification gate
- Includes source references for every claim
- Generates structured GST response draft
- Validation/reflection pass before submission to approval

---

## 6. MCP Architecture

### Tax Portal MCP Server (Port 8001)
Exposes GST portal mock data:
- `get_notice(notice_id)` — full notice record
- `get_filed_returns(gstin, tax_period)` — filed GSTR-3B/2A records
- `get_return_details(gstin, return_type, tax_period)` — return line items
- `get_vendor_filing_status(supplier_gstin, tax_period)` — GSTR-1 filing status

### Ledger MCP Server (Port 8002)
Exposes accounting ledger mock data:
- `get_entries_by_period(gstin, start_date, end_date)` — journal entries
- `get_invoice_details(invoice_id)` — full invoice record
- `search_invoices(supplier_gstin, tax_period, amount)` — invoice search
- `get_ledger_records(invoice_id, gstin, period)` — reconciliation records

---

## 7. LangGraph Workflow

```
LOAD_INVESTIGATION
      ↓
PARSE_NOTICE
      ↓
VALIDATE_NOTICE ──→ [Invalid] ──→ REQUEST_DOCUMENT
      ↓ [Valid]
BUILD_INVESTIGATION_PLAN
      ↓
CREATE_INVOICE_TASKS
      ↓
PARALLEL_LEDGER_INVESTIGATION (concurrent per invoice)
      ↓
ROOT_CAUSE_INVESTIGATION
      ↓
EVIDENCE_CHALLENGE
      ↓
VERIFICATION_GATE
      ├──→ [INSUFFICIENT] ──→ REQUEST_MORE_DOCUMENTS ──→ [Resume on upload]
      ├──→ [CONTRADICTED] ──→ ESCALATE_TO_ACCOUNTANT
      └──→ [SUPPORTED] ──→ RESPONSE_DRAFTING
                                ↓
                         ACCOUNTANT_APPROVAL
                                ↓
                         FINALIZE_INVESTIGATION
```

---

## 8. Database Architecture

24 tables organized into functional domains:

**Identity & Auth:** users, organizations, organization_members  
**Client Domain:** clients, client_gstin_profiles  
**Investigation Domain:** investigations, notices, uploaded_documents  
**Financial Records:** invoices, ledger_entries, gst_returns  
**Agent Execution:** agent_runs, tool_calls, investigation_tasks  
**Analysis:** hypotheses, evidence_records, evidence_links, evidence_assessments  
**Governance:** approvals, reports, workflow_checkpoints  
**Operations:** background_jobs, audit_logs, usage_metrics  

---

## 9. Security Architecture

- JWT access tokens (30-minute expiry), refresh token pattern
- bcrypt password hashing (cost factor 12)
- Role-based access: OWNER / ACCOUNTANT / REVIEWER
- Organization-level data isolation in all queries
- Sensitive fields (amounts, GSTINs) filtered from observability logs
- File upload validation (type, size, magic bytes)
- SQL injection prevention via SQLAlchemy ORM
- CORS restricted to known frontend origins

---

## 10. Observability

- **Langfuse** for LLM trace correlation (investigation_id as trace ID)
- Structured JSON logging per agent execution
- Token usage tracked per model call
- Estimated cost tracked (USD per 1M tokens)
- Execution duration measured at agent, node, and tool levels
- Retry count tracked
- Background job status persisted in PostgreSQL

---

## 11. Design Tokens

| Token | Value |
|-------|-------|
| Primary | #173B67 |
| Secondary | #2563A6 |
| Accent | #2E8B83 |
| Background | #F5F7FA |
| Surface | #FFFFFF |
| Main Text | #172B4D |
| Muted Text | #64748B |
| Border | #E2E8F0 |
| Success | #16845B |
| Warning | #D18A27 |
| Danger | #C44545 |
