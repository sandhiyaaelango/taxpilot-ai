import uuid
from sqlalchemy import Column, String, ForeignKey, Text, Numeric, Date, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base, TimestampMixin


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_number = Column(String(100), nullable=False, index=True)
    supplier_gstin = Column(String(15), nullable=False, index=True)
    buyer_gstin = Column(String(15), nullable=False, index=True)
    invoice_date = Column(Date, nullable=True)
    tax_period = Column(String(20), nullable=True, index=True)
    taxable_amount = Column(Numeric(15, 2), nullable=True)
    cgst_amount = Column(Numeric(15, 2), nullable=True)
    sgst_amount = Column(Numeric(15, 2), nullable=True)
    igst_amount = Column(Numeric(15, 2), nullable=True)
    total_tax = Column(Numeric(15, 2), nullable=True)
    invoice_value = Column(Numeric(15, 2), nullable=True)
    source = Column(String(50), nullable=True)  # LEDGER / GST_PORTAL / MANUAL
    is_demo = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_invoices_supplier_period", "supplier_gstin", "tax_period"),
    )


class LedgerEntry(Base, TimestampMixin):
    __tablename__ = "ledger_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_date = Column(Date, nullable=False)
    tax_period = Column(String(20), nullable=True, index=True)
    account_code = Column(String(50), nullable=True)
    account_name = Column(String(255), nullable=True)
    narration = Column(Text, nullable=True)
    debit_amount = Column(Numeric(15, 2), nullable=True)
    credit_amount = Column(Numeric(15, 2), nullable=True)
    gstin = Column(String(15), nullable=True, index=True)
    invoice_reference = Column(String(100), nullable=True)
    is_demo = Column(Boolean, default=False)


class GSTReturn(Base, TimestampMixin):
    __tablename__ = "gst_returns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    gstin = Column(String(15), nullable=False, index=True)
    return_type = Column(String(20), nullable=False)  # GSTR-1 / GSTR-2B / GSTR-3B
    tax_period = Column(String(20), nullable=False, index=True)
    filing_status = Column(String(20), nullable=True)  # FILED / NOT_FILED / PENDING
    filing_date = Column(Date, nullable=True)
    total_itc_claimed = Column(Numeric(15, 2), nullable=True)
    total_itc_available = Column(Numeric(15, 2), nullable=True)
    total_taxable_value = Column(Numeric(15, 2), nullable=True)
    is_demo = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_gst_returns_gstin_period_type", "gstin", "tax_period", "return_type"),
    )
