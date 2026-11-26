import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base, TimestampMixin


class Client(Base, TimestampMixin):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_name = Column(String(255), nullable=False)
    primary_gstin = Column(String(15), nullable=False, index=True)
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    state_code = Column(String(2), nullable=True)
    industry = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    status = Column(String(20), default="ACTIVE", nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)

    organization = relationship("Organization", back_populates="clients")
    gstin_profiles = relationship("ClientGSTINProfile", back_populates="client", cascade="all, delete-orphan")
    investigations = relationship("Investigation", back_populates="client")

    __table_args__ = (
        Index("ix_clients_org_gstin", "organization_id", "primary_gstin"),
    )


class ClientGSTINProfile(Base, TimestampMixin):
    __tablename__ = "client_gstin_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    gstin = Column(String(15), nullable=False, index=True)
    trade_name = Column(String(255), nullable=True)
    registration_type = Column(String(50), nullable=True)
    state_code = Column(String(2), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    client = relationship("Client", back_populates="gstin_profiles")
