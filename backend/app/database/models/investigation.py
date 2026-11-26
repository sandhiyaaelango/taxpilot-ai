import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Numeric, Date, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base, TimestampMixin


class Investigation(Base, TimestampMixin):
    __tablename__ = "investigations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="PENDING", nullable=False, index=True)
    workflow_state = Column(JSON, nullable=True)
    current_checkpoint_id = Column(String(255), nullable=True)
    mismatch_amount = Column(Numeric(15, 2), nullable=True)
    tax_period = Column(String(20), nullable=True)
    response_deadline = Column(Date, nullable=True)
    is_demo = Column(Boolean, default=False, nullable=False)
    idempotency_key = Column(String(255), unique=True, nullable=True)

    organization = relationship("Organization", back_populates="investigations")
    client = relationship("Client", back_populates="investigations")
    notice = relationship("Notice", back_populates="investigation", uselist=False)
    documents = relationship("UploadedDocument", back_populates="investigation")
    agent_runs = relationship("AgentRun", back_populates="investigation", order_by="AgentRun.created_at")
    investigation_tasks = relationship("InvestigationTask", back_populates="investigation")
    hypotheses = relationship("Hypothesis", back_populates="investigation")
    evidence_records = relationship("EvidenceRecord", back_populates="investigation")
    approvals = relationship("Approval", back_populates="investigation", order_by="Approval.created_at")
    reports = relationship("Report", back_populates="investigation")
    workflow_checkpoints = relationship("WorkflowCheckpoint", back_populates="investigation")
    background_jobs = relationship("BackgroundJob", back_populates="investigation")

    __table_args__ = (
        Index("ix_investigations_org_status", "organization_id", "status"),
        Index("ix_investigations_client_created", "client_id", "created_at"),
    )
