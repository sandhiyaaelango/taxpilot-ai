import uuid
from sqlalchemy import Column, String, ForeignKey, Text, Numeric, Integer, DateTime, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base, TimestampMixin


class AgentRun(Base, TimestampMixin):
    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    status = Column(String(20), default="PENDING", nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    estimated_cost_usd = Column(Numeric(10, 6), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    langfuse_trace_id = Column(String(255), nullable=True)
    agent_metadata = Column(JSON, nullable=True)

    investigation = relationship("Investigation", back_populates="agent_runs")
    tool_calls = relationship("ToolCall", back_populates="agent_run", order_by="ToolCall.called_at")


class ToolCall(Base, TimestampMixin):
    __tablename__ = "tool_calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False)
    mcp_server = Column(String(50), nullable=True)
    arguments = Column(JSON, nullable=True)
    result_summary = Column(Text, nullable=True)
    result_status = Column(String(20), nullable=False, default="PENDING")  # SUCCESS/ERROR/TIMEOUT
    duration_ms = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    called_at = Column(DateTime(timezone=True), nullable=True)

    agent_run = relationship("AgentRun", back_populates="tool_calls")


class InvestigationTask(Base, TimestampMixin):
    __tablename__ = "investigation_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    task_type = Column(String(100), nullable=False)
    subject_id = Column(String(255), nullable=True)  # invoice_id, supplier_gstin, etc.
    subject_type = Column(String(50), nullable=True)
    status = Column(String(20), default="PENDING", nullable=False)
    priority = Column(Integer, default=5, nullable=False)
    result_summary = Column(Text, nullable=True)

    investigation = relationship("Investigation", back_populates="investigation_tasks")


class BackgroundJob(Base, TimestampMixin):
    __tablename__ = "background_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=True, index=True)
    job_type = Column(String(100), nullable=False)
    status = Column(String(20), default="PENDING", nullable=False, index=True)
    idempotency_key = Column(String(255), unique=True, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    job_metadata = Column(JSON, nullable=True)

    investigation = relationship("Investigation", back_populates="background_jobs")


class WorkflowCheckpoint(Base, TimestampMixin):
    __tablename__ = "workflow_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id = Column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    checkpoint_id = Column(String(255), nullable=False)
    node_name = Column(String(100), nullable=False)
    state_data = Column(JSON, nullable=True)
    is_latest = Column(Boolean, default=True, nullable=False)

    investigation = relationship("Investigation", back_populates="workflow_checkpoints")
