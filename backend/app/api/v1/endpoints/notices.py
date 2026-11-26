import os
import uuid
import json
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.database.models.user import User
from app.database.models.client import Client
from app.database.models.notice import Notice, UploadedDocument
from app.database.models.investigation import Investigation
from app.schemas.investigation import NoticeResponse, NoticeUploadResponse
from app.schemas.common import SuccessResponse
from app.core.dependencies import get_current_user
from app.config.settings import Settings
from app.config.logging import get_logger
from app.utils.pdf_extractor import extract_text_from_pdf
from app.agents.notice_parser import NoticeParserAgent

settings = Settings()
logger = get_logger("notices_endpoint")
router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
}
MAX_FILE_SIZE = settings.max_upload_size_mb * 1024 * 1024

def _to_uuid(id_val):
    if isinstance(id_val, uuid.UUID):
        return id_val
    return uuid.UUID(str(id_val))

@router.post("/upload", response_model=SuccessResponse[NoticeUploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_notice(
    file: UploadFile = File(...),
    client_id: Optional[str] = Form(None),
    investigation_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts PDF notice uploads via multipart/form-data.
    Validates file type and size.
    Extracts text using PyMuPDF (with fallback to pypdf).
    Detects scanned PDFs and flags OCR requirements.
    Extracts structured notice data via NoticeParserAgent.
    Associates the notice with an investigation and client.
    Stores the document securely on disk and persists records to the database.
    """
    logger.info("notice_upload_initiated", filename=file.filename, content_type=file.content_type)

    # 1. Validate file existence and filename
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided")

    file_ext = Path(file.filename).suffix.lower()
    content_type = file.content_type or ""

    if file_ext not in [".pdf", ".png", ".jpg", ".jpeg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{file_ext}'. Allowed types: PDF, PNG, JPG, JPEG"
        )

    # 2. Read content and validate size
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty (0 bytes)")

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum permitted limit of {settings.max_upload_size_mb} MB"
        )

    # 3. Save original document securely
    upload_dir = Path(settings.upload_dir) / "notices"
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    saved_path = upload_dir / safe_filename

    with open(saved_path, "wb") as f:
        f.write(content)

    # 4. Extract text from document
    extraction_res = extract_text_from_pdf(str(saved_path))
    extracted_text = extraction_res.get("text", "")
    is_scanned = extraction_res.get("is_scanned", False)
    ocr_required = extraction_res.get("ocr_required", False)

    warnings = []
    if ocr_required:
        warnings.append("Document appears to be scanned or contains insufficient raw text. OCR is recommended.")

    # 5. Parse notice with NoticeParserAgent
    parser = NoticeParserAgent()
    parsed_notice = await parser.parse_text(extracted_text)

    # 6. Resolve client and investigation association
    inv = None
    if investigation_id:
        inv_query = await db.execute(
            select(Investigation).where(
                Investigation.id == _to_uuid(investigation_id),
                Investigation.organization_id == _to_uuid(current_user.organization_id)
            )
        )
        inv = inv_query.scalars().first()
        if not inv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified investigation not found in organization")
    else:
        # Determine client: from form client_id, from parsed GSTIN, or fallback to first org client
        target_client = None
        if client_id:
            c_query = await db.execute(
                select(Client).where(
                    Client.id == _to_uuid(client_id),
                    Client.organization_id == _to_uuid(current_user.organization_id)
                )
            )
            target_client = c_query.scalars().first()
        
        if not target_client and parsed_notice.gstin:
            # Search client by primary_gstin
            c_query = await db.execute(
                select(Client).where(
                    Client.primary_gstin == parsed_notice.gstin,
                    Client.organization_id == _to_uuid(current_user.organization_id)
                )
            )
            target_client = c_query.scalars().first()

        if not target_client:
            # Fallback to first active client in organization
            c_query = await db.execute(
                select(Client).where(Client.organization_id == _to_uuid(current_user.organization_id)).limit(1)
            )
            target_client = c_query.scalars().first()

        if not target_client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No registered client found in organization to associate with notice. Please register a client first."
            )

        # Create new Investigation
        inv_title = f"GST Notice Investigation - {parsed_notice.notice_number or parsed_notice.notice_type or 'ITC Mismatch'}"
        inv = Investigation(
            id=uuid.uuid4(),
            organization_id=_to_uuid(current_user.organization_id),
            client_id=target_client.id,
            created_by_id=_to_uuid(current_user.id),
            title=inv_title,
            description=f"Auto-created from uploaded {file.filename}. Notice Number: {parsed_notice.notice_number or 'Unspecified'}",
            status="PARSING_NOTICE",
            mismatch_amount=Decimal(str(parsed_notice.itc_mismatch)) if parsed_notice.itc_mismatch is not None else None,
            tax_period=parsed_notice.tax_period
        )
        db.add(inv)
        await db.flush()

    # 7. Persist UploadedDocument record
    doc_record = UploadedDocument(
        id=uuid.uuid4(),
        investigation_id=inv.id,
        uploaded_by_id=_to_uuid(current_user.id),
        filename=safe_filename,
        original_filename=file.filename,
        file_path=str(saved_path),
        file_size_bytes=Decimal(file_size),
        content_type=content_type,
        document_type="NOTICE",
        processing_status="EXTRACTED" if not ocr_required else "NEEDS_OCR",
        extracted_text=extracted_text[:10000] if extracted_text else ""
    )
    db.add(doc_record)

    # 8. Create or update Notice record
    existing_notice_q = await db.execute(select(Notice).where(Notice.investigation_id == inv.id))
    db_notice = existing_notice_q.scalars().first()

    # Parse deadline if string
    parsed_deadline = None
    if parsed_notice.response_deadline:
        try:
            parsed_deadline = datetime.strptime(parsed_notice.response_deadline, "%Y-%m-%d").date()
        except Exception:
            pass

    parsed_issued = None
    if parsed_notice.issued_date:
        try:
            parsed_issued = datetime.strptime(parsed_notice.issued_date, "%Y-%m-%d").date()
        except Exception:
            pass

    notice_status = "VALIDATED" if parsed_notice.gstin and parsed_notice.itc_mismatch is not None else ("PARSED" if parsed_notice.raw_text else "INVALID")
    if not parsed_notice.gstin:
        warnings.append("Notice does not contain a verified 15-character GSTIN.")

    if db_notice:
        db_notice.notice_number = parsed_notice.notice_number or db_notice.notice_number
        db_notice.notice_type = parsed_notice.notice_type or db_notice.notice_type
        db_notice.gstin = parsed_notice.gstin or db_notice.gstin
        db_notice.tax_period = parsed_notice.tax_period or db_notice.tax_period
        db_notice.itc_claimed = Decimal(str(parsed_notice.itc_claimed)) if parsed_notice.itc_claimed is not None else db_notice.itc_claimed
        db_notice.itc_available = Decimal(str(parsed_notice.itc_available)) if parsed_notice.itc_available is not None else db_notice.itc_available
        db_notice.itc_mismatch = Decimal(str(parsed_notice.itc_mismatch)) if parsed_notice.itc_mismatch is not None else db_notice.itc_mismatch
        db_notice.response_deadline = parsed_deadline or db_notice.response_deadline
        db_notice.issued_date = parsed_issued or db_notice.issued_date
        db_notice.issuing_authority = parsed_notice.issuing_authority or db_notice.issuing_authority
        db_notice.raw_text = extracted_text or db_notice.raw_text
        db_notice.extraction_confidence = parsed_notice.extraction_confidence
        db_notice.uncertain_fields = json.dumps(parsed_notice.uncertain_fields)
        db_notice.status = notice_status
    else:
        db_notice = Notice(
            id=uuid.uuid4(),
            investigation_id=inv.id,
            notice_number=parsed_notice.notice_number,
            notice_type=parsed_notice.notice_type,
            gstin=parsed_notice.gstin,
            tax_period=parsed_notice.tax_period,
            itc_claimed=Decimal(str(parsed_notice.itc_claimed)) if parsed_notice.itc_claimed is not None else None,
            itc_available=Decimal(str(parsed_notice.itc_available)) if parsed_notice.itc_available is not None else None,
            itc_mismatch=Decimal(str(parsed_notice.itc_mismatch)) if parsed_notice.itc_mismatch is not None else None,
            response_deadline=parsed_deadline,
            issued_date=parsed_issued,
            issuing_authority=parsed_notice.issuing_authority,
            raw_text=extracted_text,
            extraction_confidence=parsed_notice.extraction_confidence,
            uncertain_fields=json.dumps(parsed_notice.uncertain_fields),
            status=notice_status
        )
        db.add(db_notice)

    # Sync investigation metadata
    if parsed_notice.itc_mismatch is not None:
        inv.mismatch_amount = Decimal(str(parsed_notice.itc_mismatch))
    if parsed_notice.tax_period:
        inv.tax_period = parsed_notice.tax_period
    if parsed_deadline:
        inv.response_deadline = parsed_deadline
    inv.status = "BUILDING_PLAN" if notice_status in ["PARSED", "VALIDATED"] else "PENDING"

    await db.commit()
    await db.refresh(inv)
    await db.refresh(db_notice)

    # Phase 7: Audit trail — log notice upload
    try:
        from app.database.repositories.audit_repository import AuditRepository
        audit_repo = AuditRepository(db)
        await audit_repo.log_action(
            action="NOTICE_UPLOADED",
            resource_type="notice",
            resource_id=str(db_notice.id),
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id),
            details={
                "notice_number": parsed_notice.notice_number,
                "gstin": parsed_notice.gstin,
                "itc_mismatch": parsed_notice.itc_mismatch,
                "tax_period": parsed_notice.tax_period,
                "investigation_id": str(inv.id),
                "filename": file.filename,
            }
        )
        await db.commit()
    except Exception:
        pass  # Audit failure must never block upload

    notice_resp = NoticeResponse(
        id=str(db_notice.id),
        investigation_id=str(db_notice.investigation_id),
        notice_number=db_notice.notice_number,
        notice_type=db_notice.notice_type,
        gstin=db_notice.gstin,
        tax_period=db_notice.tax_period,
        itc_claimed=float(db_notice.itc_claimed) if db_notice.itc_claimed else None,
        itc_available=float(db_notice.itc_available) if db_notice.itc_available else None,
        itc_mismatch=float(db_notice.itc_mismatch) if db_notice.itc_mismatch else None,
        response_deadline=db_notice.response_deadline,
        issued_date=db_notice.issued_date,
        issuing_authority=db_notice.issuing_authority,
        extraction_confidence=db_notice.extraction_confidence,
        status=db_notice.status
    )

    upload_result = NoticeUploadResponse(
        document_id=str(doc_record.id),
        investigation_id=str(inv.id),
        filename=file.filename,
        file_size_bytes=file_size,
        is_scanned=is_scanned,
        ocr_required=ocr_required,
        notice=notice_resp,
        validation_status=notice_status,
        warnings=warnings
    )

    return SuccessResponse(
        data=upload_result,
        message="Notice uploaded, parsed, and associated successfully"
    )

@router.get("/{notice_id}", response_model=SuccessResponse[NoticeResponse])
async def get_notice(
    notice_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = await db.execute(select(Notice).where(Notice.notice_number == notice_id))
    notice = query.scalars().first()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")

    return SuccessResponse(
        data=NoticeResponse(
            id=str(notice.id),
            investigation_id=str(notice.investigation_id),
            notice_number=notice.notice_number,
            notice_type=notice.notice_type,
            gstin=notice.gstin,
            tax_period=notice.tax_period,
            itc_claimed=float(notice.itc_claimed) if notice.itc_claimed else None,
            itc_available=float(notice.itc_available) if notice.itc_available else None,
            itc_mismatch=float(notice.itc_mismatch) if notice.itc_mismatch else None,
            response_deadline=notice.response_deadline,
            issued_date=notice.issued_date,
            issuing_authority=notice.issuing_authority,
            extraction_confidence=notice.extraction_confidence,
            status=notice.status
        )
    )
