import uuid
from sqlalchemy import Column, String, ForeignKey, Text, Numeric, Float, Boolean, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base, TimestampMixin


class Hypothesis(Base, TimestampMixin):
    __tablename__ = "hypotheses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    hypothesis_type = Column(String(50), nullable=False)  # TIMING_DIFFERENCE, DUPLICATE_INVOICE, etc.
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="PENDING", nullable=False)  # SUPPORTED/CONTRADICTED/UNVERIFIED/PENDING
    confidence_score = Column(Float, nullable=True)
    supporting_evidence_count = Column(Numeric(5, 0), default=0, nullable=False)
    contradicting_evidence_count = Column(Numeric(5, 0), default=0, nullable=False)
    missing_evidence_description = Column(Text, nullable=True)
    investigator_rationale = Column(Text, nullable=True)
    challenge_rationale = Column(Text, nullable=True)

    investigation = relationship("Investigation", back_populates="hypotheses")
    evidence_records = relationship("EvidenceRecord", secondary="evidence_links", back_populates="hypotheses")
    assessments = relationship("EvidenceAssessment", back_populates="hypothesis")


class EvidenceRecord(Base, TimestampMixin):
    __tablename__ = "evidence_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(String(255), nullable=False)  # ID from MCP server or database
    source_type = Column(String(50), nullable=False)  # INVOICE/LEDGER_ENTRY/GST_RETURN/SUPPLIER_FILING/NOTICE
    document_name = Column(String(500), nullable=True)
    amount = Column(Numeric(15, 2), nullable=True)
    tax_period = Column(String(20), nullable=True)
    gstin = Column(String(15), nullable=True)
    record_date = Column(DateTime(timezone=True), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), nullable=True)
    retrieved_by = Column(String(100), nullable=True)  # agent name
    mcp_server = Column(String(50), nullable=True)
    raw_data = Column(JSON, nullable=True)
    status = Column(String(20), default="PENDING", nullable=False)
    verification_notes = Column(Text, nullable=True)

    investigation = relationship("Investigation", back_populates="evidence_records")
    hypotheses = relationship("Hypothesis", secondary="evidence_links", back_populates="evidence_records")

    __table_args__ = (
        Index("ix_evidence_records_inv_source", "investigation_id", "source_type"),
    )


class EvidenceLink(Base):
    __tablename__ = "evidence_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hypothesis_id = Column(UUID(as_uuid=True), ForeignKey("hypotheses.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_record_id = Column(UUID(as_uuid=True), ForeignKey("evidence_records.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(30), nullable=False)  # SUPPORTS / CONTRADICTS / REFERENCED
    relationship_reason = Column(Text, nullable=True)


class EvidenceAssessment(Base, TimestampMixin):
    __tablename__ = "evidence_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hypothesis_id = Column(UUID(as_uuid=True), ForeignKey("hypotheses.id", ondelete="CASCADE"), nullable=False, index=True)
    assessed_by = Column(String(100), nullable=False)  # agent name
    assessment_type = Column(String(50), nullable=False)  # ROOT_CAUSE / EVIDENCE_CHALLENGE
    result = Column(String(20), nullable=False)  # SUPPORTED/CONTRADICTED/UNVERIFIED
    rationale = Column(Text, nullable=True)
    evidence_gaps = Column(Text, nullable=True)  # JSON list

    hypothesis = relationship("Hypothesis", back_populates="assessments")
