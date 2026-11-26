import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SAEnum("AUDITOR", "ADMIN", "OWNER", "ACCOUNTANT", "REVIEWER", name="user_role"), nullable=False, default="AUDITOR")
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    organization = relationship("Organization", back_populates="members")
    organization_memberships = relationship("OrganizationMember", back_populates="user")
    approvals = relationship("Approval", back_populates="reviewer")
    audit_logs = relationship("AuditLog", back_populates="user")
