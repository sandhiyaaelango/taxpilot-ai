import uuid
from sqlalchemy import Column, String, ForeignKey, Text, Numeric, Date, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base, TimestampMixin


class Notice(Base, TimestampMixin):
    __tablename__ = "notices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    notice_number = Column(String(100), nullable=True, index=True)
    notice_type = Column(String(100), nullable=True)
    gstin = Column(String(15), nullable=True, index=True)
    tax_period = Column(String(20), nullable=True)
    itc_claimed = Column(Numeric(15, 2), nullable=True)
    itc_available = Column(Numeric(15, 2), nullable=True)
    itc_mismatch = Column(Numeric(15, 2), nullable=True)
    response_deadline = Column(Date, nullable=True)
    issued_date = Column(Date, nullable=True)
    issuing_authority = Column(String(255), nullable=True)
    raw_text = Column(Text, nullable=True)
    extraction_confidence = Column(Float, nullable=True)
    uncertain_fields = Column(Text, nullable=True)  # JSON list of uncertain field names
    status = Column(String(20), default="PENDING", nullable=False)  # PENDING/PARSED/VALIDATED/INVALID
    validation_notes = Column(Text, nullable=True)

    investigation = relationship("Investigation", back_populates="notice")


class UploadedDocument(Base, TimestampMixin):
    __tablename__ = "uploaded_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size_bytes = Column(Numeric(15, 0), nullable=True)
    content_type = Column(String(100), nullable=True)
    document_type = Column(String(50), nullable=True)  # NOTICE / INVOICE / LEDGER / OTHER
    processing_status = Column(String(20), default="PENDING", nullable=False)
    extracted_text = Column(Text, nullable=True)

    investigation = relationship("Investigation", back_populates="documents")
