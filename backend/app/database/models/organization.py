import uuid
from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base, TimestampMixin


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    plan = Column(String(50), default="DEMO", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(Text, nullable=True)  # JSON string

    members = relationship("User", back_populates="organization")
    organization_members = relationship("OrganizationMember", back_populates="organization")
    clients = relationship("Client", back_populates="organization")
    investigations = relationship("Investigation", back_populates="organization")


class OrganizationMember(Base, TimestampMixin):
    __tablename__ = "organization_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="ACCOUNTANT")
    is_active = Column(Boolean, default=True)

    organization = relationship("Organization", back_populates="organization_members")
    user = relationship("User", back_populates="organization_memberships")
