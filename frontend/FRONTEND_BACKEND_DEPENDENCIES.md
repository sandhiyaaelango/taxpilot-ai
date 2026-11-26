# TaxPilot AI — Frontend & Backend Dependencies Report

This document records backend API contracts, observed mismatches, and verification status for frontend-backend integrations. Per project rules, no backend files were modified.

---

## 1. Status Classification

| Flow / Integration | Status | Notes |
|---|---|---|
| **TypeScript & Vite Production Build (`npm run build`)** | **PASS** | Compiled with 0 errors (`2170 modules transformed`). |
| **Sign In (`POST /api/v1/auth/login`)** | **NOT TESTED** | Backend server on `localhost:8000` was not running during final verification. |
| **PDF Upload & Extraction (`POST /api/v1/notices/upload`)** | **NOT TESTED** | Frontend fixed to read `res.data.data.notice` (was reading `extracted_notice`). Live API call not executed because backend was offline. |
| **Manual Text Notice Upload (`POST /api/v1/investigations/{id}/notice`)** | **NOT TESTED** | Frontend fixed from `/upload-notice-text` JSON to `/notice` `multipart/form-data`. Live API call not executed. |
| **Start AI Investigation (`POST /api/v1/investigations/{id}/run`)** | **NOT TESTED** | Preserved with `Idempotency-Key` header. Backend offline during final check. |
| **AI Monitoring & SSE (`GET /api/v1/investigations/{id}/stream`)** | **NOT TESTED** | Preserved existing `EventSource` + 3s polling fallback. |
| **Investigation Results & Evidence (`GET /investigations/{id}`, `/evidence`)** | **NOT TESTED** | Preserved existing API calls. |
| **Save Response Draft (`PATCH /api/v1/reports/{id}` / existing draft endpoint)** | **NOT TESTED** | Preserved existing API integration. |
| **Investigation History (`GET /api/v1/investigations`)** | **NOT TESTED** | Preserved existing paginated endpoint. |
| **Auditor Approval (`POST /api/v1/approvals/{id}`)** | **NOT TESTED** | Preserved existing approval actions (`APPROVE`, `REJECT`, `REQUEST_MORE_EVIDENCE`). |
| **PDF Export / Download (`GET /api/v1/reports/{id}/download`)** | **BLOCKED (Live Download Not Executed)** | Frontend Blob error parsing, `%PDF-` magic-header validation, filename extraction, and delayed `revokeObjectURL` fixed in `src/utils/pdfDownload.ts`. Live PDF download not executed because backend (`localhost:8000`) is offline and `.venv` Python path is unavailable on this machine. |
| **Role-Based Navigation (`AUDITOR` vs `ADMIN` / `OWNER`)** | **PASS (Static)** | Verified in `router.tsx` and `Sidebar.tsx` without modifying backend permissions. |

---

## 2. Documented Backend Schema / Contract Gaps (Observed by Reading Backend Code)

1. **PDF Extraction Response Schema (`NoticeUploadResponse` / `NoticeResponse`)**:
   - `POST /api/v1/notices/upload` returns `NoticeResponse` fields: `notice_number`, `notice_type`, `gstin`, `tax_period`, `itc_claimed`, `itc_available`, `itc_mismatch`, `response_deadline`, `issued_date`, `issuing_authority`, `extraction_confidence`, `status`.
   - **Missing fields on `NoticeResponse`**: `taxpayer_name`, `financial_year`, `section`, and `tax_type` are not returned as dedicated fields by the backend schema.
   - **Frontend handling (no backend modification)**: `taxpayerName` is populated from the matched `Client.business_name` in `/api/v1/clients`, `financialYear` is derived client-side from `tax_period` when in `YYYY-MM` format, and `section` / `tax_type` remain editable by the auditor in the verification form.

2. **Persisting Auditor Edits to Extracted Notice Fields (`PATCH /api/v1/investigations/{id}`)**:
   - `InvestigationUpdate` schema in `backend/app/schemas/investigation.py` only accepts `title`, `description`, `status`, and `response_deadline`.
   - There is no `PATCH /api/v1/notices/{id}` endpoint in `backend/app/api/v1/endpoints/notices.py` to persist auditor edits to `gstin`, `notice_number`, `notice_type`, `tax_period`, or `itc_mismatch` after upload.
   - **Frontend handling**: `AuditorNewInvestigationPage.tsx` persists `title`, `description`, and `response_deadline` via `PATCH /api/v1/investigations/{id}` before calling `POST /api/v1/investigations/{id}/run`. Auditor edits to `gstin`, `notice_number`, `notice_type`, `tax_period`, and `itc_mismatch` are validated on the frontend but cannot be written back to `Notice` without a backend `PATCH /notices/{id}` endpoint.

3. **PDF Export Flow (`GET /api/v1/reports/{id}/download`)**:
   - **Endpoint & Method**: `GET /api/v1/reports/{id}/download` (with `Authorization: Bearer <token>` and `responseType: 'blob'`).
   - **Backend Precondition (`reports.py:117-121`)**: Strictly requires `inv.status == "APPROVED"`; otherwise returns `HTTP 400` JSON (`{"detail": "Final PDF report is only available after Auditor approval (current status: <status>)."}`).
   - **Root Cause of Generic Frontend Error**: When Axios requests `responseType: 'blob'`, HTTP error responses (`400`, `401`, `403`, `404`, `500`) arrive with `err.response.data` as a `Blob` rather than a parsed JSON object, making `err.response?.data?.detail` `undefined` and always displaying `"Failed to generate or download PDF report."`
   - **Frontend Fixes Applied**:
     - Added `src/utils/pdfDownload.ts` (`downloadReportPdf`, `extractApiErrorMessage`) to parse `Blob` error responses into real backend error messages, validate non-empty `%PDF-` magic headers, extract `Content-Disposition` filenames, and delay `URL.revokeObjectURL` by `1000ms`.
     - Updated `AuditorPendingReviewPage.tsx` and `AuditorApprovedReportsPage.tsx` with duplicate-click prevention, `"Generating PDF..."` loading state, toast success notification, real API error display, and a Retry button.
   - **Unresolved Environment Blocker**: Backend server at `http://localhost:8000` is not running and `backend/.venv/Scripts/python.exe` points to a missing interpreter path (`C:\Users\ganes\AppData\Local\Programs\Python\Python311\python.exe`), preventing live end-to-end PDF download testing in this environment.
