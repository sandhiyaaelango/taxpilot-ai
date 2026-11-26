import uuid
from sqlalchemy import Column, String, ForeignKey, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base, TimestampMixin


class Approval(Base, TimestampMixin):
    __tablename__ = "approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(30), nullable=False)  # APPROVE/EDIT/REJECT/REQUEST_MORE_EVIDENCE
    notes = Column(Text, nullable=True)
    edited_content = Column(JSON, nullable=True)
    is_final = Column(Boolean, default=False, nullable=False)

    investigation = relationship("Investigation", back_populates="approvals")
    reviewer = relationship("User", back_populates="approvals")


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(String(50), nullable=False)  # INVESTIGATION/RESPONSE_DRAFT/FINAL
    title = Column(String(500), nullable=False)
    content = Column(JSON, nullable=True)
    pdf_path = Column(String(1000), nullable=True)
    is_latest = Column(Boolean, default=True, nullable=False)
    generated_by = Column(String(100), nullable=True)

    investigation = relationship("Investigation", back_populates="reports")
