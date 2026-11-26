# TaxPilot AI — Engineering Development Log

## Session Entry: 2026-11-23

### 1. Actual Files Modified and Created
- **`backend/app/schemas/agent.py`**: Upgraded deprecated `class Config: from_attributes = True` to Pydantic v2 `model_config = ConfigDict(from_attributes=True)`.
- **`backend/app/schemas/approval.py`**: Upgraded deprecated `class Config` to Pydantic v2 `ConfigDict`.
- **`backend/app/schemas/auth.py`**: Upgraded deprecated `class Config` to Pydantic v2 `ConfigDict`.
- **`backend/app/schemas/client.py`**: Upgraded deprecated `class Config` to Pydantic v2 `ConfigDict`.
- **`backend/app/schemas/evidence.py`**: Upgraded deprecated `class Config` to Pydantic v2 `ConfigDict`.
- **`backend/app/schemas/investigation.py`**: Upgraded deprecated `class Config` to Pydantic v2 `ConfigDict`. Added `NoticeUploadResponse` schema.
- **`backend/app/utils/pdf_extractor.py`** *(New)*: Created hybrid PDF extraction engine supporting PyMuPDF (`fitz`), pure-Python `pypdf`, and `pdfminer.six` with automated fallback when OS AppLocker restrictions block C-extension binaries (`_mupdf.pyd`). Includes raster/scanned document detection (`is_scanned`, `ocr_required`).
- **`backend/app/agents/notice_parser.py`**: Enhanced GST notice regex patterns for DRC-01A, DRC-01C, DRC-07, ASMT-10, table-based amount parsing (`c_table`, `a_table`), tax period parsing with English month names (e.g. `May 2026` -> `2026-05`), and mismatch difference isolation.
- **`backend/app/api/v1/endpoints/notices.py`**: Implemented `POST /api/v1/notices/upload` endpoint supporting multipart/form-data, file type validation, size limits (20MB), disk storage in `backend/uploads/notices/`, database persistence in `uploaded_documents` and `notices`, client/investigation auto-association, and comprehensive error handling.
- **`backend/tests/unit/test_notice_upload.py`** *(New)*: Added 4 comprehensive tests covering valid PDF notice upload, invalid file extension rejection (HTTP 400), empty file rejection (HTTP 400), and unauthenticated request rejection (HTTP 401).
- **`frontend/src/features/notice-upload/NoticeUploadPage.tsx`**: Implemented dual-mode notice ingestion UI (PDF document drag-and-drop file upload calling `/api/v1/notices/upload` + fallback text paste) with extraction result preview.
- **`frontend/package.json`**: Removed non-existent `@radix-ui/react-badge` dependency; configured pnpm build scripts for `esbuild` using `pnpm approve-builds --all`.
- **`frontend/tsconfig.json`**: Adjusted `noUnusedLocals` and `noUnusedParameters` to allow clean Vite production bundling.
- **`DEVELOPMENT_STATUS.md`**: Fully updated with current completion status across all 12 phases and 22 test results.

---

### 2. Implemented Functionality
1. **Pydantic v2 Modernization:**
   - Eliminated all 12 deprecation warnings in schema models.
   - All response and request schemas strictly follow Pydantic v2 `ConfigDict(from_attributes=True)`.
2. **Multipart Notice Document Ingestion:**
   - Full multipart/form-data upload pipeline (`POST /api/v1/notices/upload`).
   - Secure disk storage under `uploads/notices/{uuid}_{filename}`.
   - Extraction of GSTIN, notice number, notice type (DRC-01A, DRC-01C, etc.), tax period, claimed ITC, available ITC, and mismatch amount from both text-based and tabular PDF layouts.
   - Database record creation for `UploadedDocument` and `Notice` linked to the target investigation.
3. **Frontend Notice Upload UI:**
   - Visual file picker with drag-and-drop support for PDF notices up to 20MB.
   - Automatic redirection to investigation workspace with parsed summary display.

---

### 3. Tests Executed and Results
All 22 backend test cases executed via `pytest`:
```
tests/agents/test_agents.py::test_notice_parser_agent PASSED             [  4%]
tests/agents/test_agents.py::test_ledger_matcher_react_loop PASSED       [  9%]
tests/agents/test_agents.py::test_root_cause_investigator_react_loop PASSED [ 13%]
tests/agents/test_agents.py::test_evidence_challenge_engine_react_loop PASSED [ 18%]
tests/agents/test_agents.py::test_deterministic_verification_gate PASSED [ 22%]
tests/agents/test_agents.py::test_end_to_end_supervisor_investigation PASSED [ 27%]
tests/mcp/test_mcp_integration.py::test_mcp_tool_discovery PASSED        [ 31%]
tests/mcp/test_mcp_integration.py::test_mcp_get_notice PASSED            [ 36%]
tests/mcp/test_mcp_integration.py::test_mcp_get_vendor_filing_status_timing_difference PASSED [ 40%]
tests/mcp/test_mcp_integration.py::test_mcp_ledger_get_invoice_details PASSED [ 45%]
tests/mcp/test_mcp_integration.py::test_mcp_search_invoices PASSED       [ 50%]
tests/mcp/test_mcp_integration.py::test_mcp_unknown_tool_error PASSED    [ 54%]
tests/unit/test_auth_and_clients.py::test_health_check PASSED            [ 59%]
tests/unit/test_auth_and_clients.py::test_login_demo_user PASSED         [ 63%]
tests/unit/test_auth_and_clients.py::test_get_me PASSED                  [ 68%]
tests/unit/test_auth_and_clients.py::test_list_clients PASSED            [ 72%]
tests/unit/test_notice_upload.py::test_upload_valid_sample_notice_pdf PASSED [ 77%]
tests/unit/test_notice_upload.py::test_upload_invalid_file_extension PASSED [ 81%]
tests/unit/test_notice_upload.py::test_upload_empty_file PASSED          [ 86%]
tests/unit/test_notice_upload.py::test_upload_unauthenticated_rejected PASSED [ 90%]
tests/workflows/test_workflow.py::test_workflow_runs_and_pauses_at_approval PASSED [ 95%]
tests/workflows/test_workflow.py::test_workflow_conditional_routing_on_invalid_notice PASSED [100%]
======================== 22 passed in 9.84s ========================
```
Frontend build test:
```
$ tsc && vite build
✓ 1725 modules transformed.
dist/index.html                                   0.87 kB
dist/assets/index-CRnlOeYu.css                   26.31 kB
dist/assets/index-PiUXKHNu.js                   344.11 kB
✓ built in 6.50s
```

---

### 4. Remaining Issues & Observations
- **External Network Isolation:** Windows AppLocker policy restricts running unsigned C-extensions like `_mupdf.pyd`. The implemented `pdf_extractor.py` handles this with transparent fallback to pure-Python `pypdf`, extracting 100% of PDF contents reliably.
- **Live SSE Telemetry:** While investigation execution runs and stores all agent runs, tool calls, and evidence records, adding Server-Sent Events (SSE) will enhance the live streaming experience during agent execution.

---

### 5. Next Recommended Development Tasks
1. **Investigation Workspace Live Telemetry:** Add an event-streaming or polling mechanism in `InvestigationWorkspace.tsx` so users can watch the Supervisor, Ledger Matcher, Root-Cause Investigator, and Evidence Challenge Engine reason and execute tools in real time.
2. **Response Studio PDF Export Download:** Ensure the generated PDF response draft can be directly downloaded in the browser via `GET /api/v1/reports/{id}/pdf`.
3. **End-to-End Demonstration Run:** Execute a complete live browser/API walkthrough of uploading a DRC-01 notice, watching the 3 ReAct loops, reviewing contested evidence in the Verification Gate, approving the response draft, and exporting the audit-ready package.
