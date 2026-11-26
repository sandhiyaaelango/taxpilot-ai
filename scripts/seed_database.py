import asyncio
import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
import sys
import os

# Ensure backend directory is in python path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_dir)

from app.database.session import async_engine, AsyncSessionLocal
from app.database.base import Base
from app.database.models import (
    User, Organization, OrganizationMember, Client, ClientGSTINProfile,
    Investigation, Notice, Invoice, LedgerEntry, GSTReturn,
    Hypothesis, EvidenceRecord, EvidenceLink, EvidenceAssessment, Approval, Report, AuditLog
)
from app.config.security import hash_password
from app.config.logging import get_logger

logger = get_logger("seed_database")

async def seed_data():
    logger.info("starting_database_seeding")

    # 1. Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        from sqlalchemy import select
        existing_org = await session.execute(select(Organization).where(Organization.slug == "abc-traders-ca"))
        if existing_org.scalars().first():
            logger.info("database_already_seeded_skipping")
            return

        # 2. Organization
        org_id = uuid.uuid4()
        org = Organization(
            id=org_id,
            name="ABC Traders & Co Chartered Accountants",
            slug="abc-traders-ca",
            plan="ENTERPRISE",
            is_active=True
        )
        session.add(org)

        # 3. Users
        owner_id = uuid.uuid4()
        owner = User(
            id=owner_id,
            email="admin@abctraders.demo",
            hashed_password=hash_password("TaxPilot@2024"),
            full_name="Rajesh Sharma (Partner)",
            role="OWNER",
            organization_id=org_id,
            is_active=True,
            is_verified=True
        )
        session.add(owner)

        accountant_id = uuid.uuid4()
        accountant = User(
            id=accountant_id,
            email="ca@abctraders.demo",
            hashed_password=hash_password("TaxPilot@2024"),
            full_name="Pooja Mehta (Senior CA)",
            role="ACCOUNTANT",
            organization_id=org_id,
            is_active=True,
            is_verified=True
        )
        session.add(accountant)

        reviewer_id = uuid.uuid4()
        reviewer = User(
            id=reviewer_id,
            email="reviewer@abctraders.demo",
            hashed_password=hash_password("TaxPilot@2024"),
            full_name="Anil Verma (Tax Auditor)",
            role="REVIEWER",
            organization_id=org_id,
            is_active=True,
            is_verified=True
        )
        session.add(reviewer)

        # Memberships
        session.add(OrganizationMember(organization_id=org_id, user_id=owner_id, role="OWNER"))
        session.add(OrganizationMember(organization_id=org_id, user_id=accountant_id, role="ACCOUNTANT"))
        session.add(OrganizationMember(organization_id=org_id, user_id=reviewer_id, role="REVIEWER"))

        # 4. Clients
        client_id = uuid.uuid4()
        client = Client(
            id=client_id,
            organization_id=org_id,
            business_name="ABC Traders Pvt Ltd",
            primary_gstin="27AABCT1234C1Z5",
            contact_name="Vikram Patel",
            contact_email="accounts@abctraders.com",
            contact_phone="+91 98200 12345",
            state_code="27",
            industry="Wholesale & Distribution",
            address="Plot 45, MIDC Industrial Area, Andheri East, Mumbai, Maharashtra 400093",
            status="ACTIVE",
            is_demo=True
        )
        session.add(client)

        session.add(ClientGSTINProfile(
            client_id=client_id,
            gstin="27AABCT1234C1Z5",
            trade_name="ABC Traders",
            registration_type="Regular",
            state_code="27",
            is_primary=True,
            is_active=True
        ))

        # Client 2
        client2_id = uuid.uuid4()
        client2 = Client(
            id=client2_id,
            organization_id=org_id,
            business_name="Zenith Infra Technologies Ltd",
            primary_gstin="29AAACZ9876D1Z2",
            contact_name="Deepak Rao",
            contact_email="finance@zenithinfra.in",
            contact_phone="+91 98450 67890",
            state_code="29",
            industry="Software & IT Infrastructure",
            address="Cyber Towers, Whitefield, Bengaluru, Karnataka 560066",
            status="ACTIVE",
            is_demo=True
        )
        session.add(client2)

        # 5. Invoices (Mathematically consistent synthetic records)
        invoices = [
            Invoice(
                id=uuid.uuid4(),
                organization_id=org_id,
                client_id=client_id,
                invoice_number="INV-2023-0891",
                supplier_gstin="27AABCS5555D1Z8",  # Apex Logistics
                buyer_gstin="27AABCT1234C1Z5",
                invoice_date=date(2023, 11, 28),
                tax_period="2023-11",
                taxable_amount=Decimal("450000.00"),
                cgst_amount=Decimal("40500.00"),
                sgst_amount=Decimal("40500.00"),
                igst_amount=Decimal("0.00"),
                total_tax=Decimal("81000.00"),
                invoice_value=Decimal("531000.00"),
                source="LEDGER",
                is_demo=True
            ),
            Invoice(
                id=uuid.uuid4(),
                organization_id=org_id,
                client_id=client_id,
                invoice_number="INV-2023-0892",
                supplier_gstin="27AABCS5555D1Z8",  # Apex Logistics - Duplicate booking
                buyer_gstin="27AABCT1234C1Z5",
                invoice_date=date(2023, 11, 28),
                tax_period="2023-11",
                taxable_amount=Decimal("450000.00"),
                cgst_amount=Decimal("40500.00"),
                sgst_amount=Decimal("40500.00"),
                igst_amount=Decimal("0.00"),
                total_tax=Decimal("81000.00"),
                invoice_value=Decimal("531000.00"),
                source="LEDGER",
                is_demo=True
            ),
            Invoice(
                id=uuid.uuid4(),
                organization_id=org_id,
                client_id=client_id,
                invoice_number="DL-8841",
                supplier_gstin="07AAACD7777E1Z3",  # Delta Electricals
                buyer_gstin="27AABCT1234C1Z5",
                invoice_date=date(2023, 11, 15),
                tax_period="2023-11",
                taxable_amount=Decimal("320000.00"),
                cgst_amount=Decimal("0.00"),
                sgst_amount=Decimal("0.00"),
                igst_amount=Decimal("57600.00"),
                total_tax=Decimal("57600.00"),
                invoice_value=Decimal("377600.00"),
                source="LEDGER",
                is_demo=True
            ),
            Invoice(
                id=uuid.uuid4(),
                organization_id=org_id,
                client_id=client_id,
                invoice_number="SP-5501",
                supplier_gstin="27AAACS1111B1Z2",  # Surya Packaging
                buyer_gstin="27AABCT1234C1Z5",
                invoice_date=date(2023, 10, 31),
                tax_period="2023-10",
                taxable_amount=Decimal("200000.00"),
                cgst_amount=Decimal("18000.00"),
                sgst_amount=Decimal("18000.00"),
                igst_amount=Decimal("0.00"),
                total_tax=Decimal("36000.00"),
                invoice_value=Decimal("236000.00"),
                source="LEDGER",
                is_demo=True
            ),
        ]
        for inv in invoices:
            session.add(inv)

        # 6. Ledger Entries
        ledgers = [
            LedgerEntry(
                id=uuid.uuid4(),
                organization_id=org_id,
                client_id=client_id,
                entry_date=date(2023, 11, 30),
                tax_period="2023-11",
                account_code="ITC-INPUT-CGST",
                account_name="Input CGST Ledger",
                narration="Input credit on Apex Logistics INV-2023-0891",
                debit_amount=Decimal("40500.00"),
                credit_amount=Decimal("0.00"),
                gstin="27AABCT1234C1Z5",
                invoice_reference="INV-2023-0891",
                is_demo=True
            ),
            LedgerEntry(
                id=uuid.uuid4(),
                organization_id=org_id,
                client_id=client_id,
                entry_date=date(2023, 11, 30),
                tax_period="2023-11",
                account_code="ITC-INPUT-SGST",
                account_name="Input SGST Ledger",
                narration="Input credit on Apex Logistics INV-2023-0891",
                debit_amount=Decimal("40500.00"),
                credit_amount=Decimal("0.00"),
                gstin="27AABCT1234C1Z5",
                invoice_reference="INV-2023-0891",
                is_demo=True
            ),
            LedgerEntry(
                id=uuid.uuid4(),
                organization_id=org_id,
                client_id=client_id,
                entry_date=date(2023, 11, 30),
                tax_period="2023-11",
                account_code="ITC-INPUT-IGST",
                account_name="Input IGST Ledger",
                narration="Input credit on Delta Electricals DL-8841",
                debit_amount=Decimal("57600.00"),
                credit_amount=Decimal("0.00"),
                gstin="27AABCT1234C1Z5",
                invoice_reference="DL-8841",
                is_demo=True
            ),
        ]
        for led in ledgers:
            session.add(led)

        # 7. GST Returns
        returns = [
            GSTReturn(
                id=uuid.uuid4(),
                organization_id=org_id,
                client_id=client_id,
                gstin="27AABCT1234C1Z5",
                return_type="GSTR-3B",
                tax_period="2023-11",
                filing_status="FILED",
                filing_date=date(2023, 12, 20),
                total_itc_claimed=Decimal("174600.00"),
                total_itc_available=Decimal("174600.00"),
                total_taxable_value=Decimal("970000.00"),
                is_demo=True
            ),
            GSTReturn(
                id=uuid.uuid4(),
                organization_id=org_id,
                client_id=client_id,
                gstin="27AABCT1234C1Z5",
                return_type="GSTR-2B",
                tax_period="2023-11",
                filing_status="AVAILABLE",
                filing_date=date(2023, 12, 14),
                total_itc_claimed=Decimal("0.00"),
                total_itc_available=Decimal("93600.00"),  # Mismatch: 174600 - 93600 = 81000
                total_taxable_value=Decimal("520000.00"),
                is_demo=True
            )
        ]
        for ret in returns:
            session.add(ret)

        # 8. Primary Investigation (Scenario 1: Supported Timing Difference & Non-Filing)
        inv1_id = uuid.uuid4()
        inv1 = Investigation(
            id=inv1_id,
            organization_id=org_id,
            client_id=client_id,
            created_by_id=accountant_id,
            title="GST DRC-01A ITC Mismatch FY 2023-24 (Nov 2023)",
            description="Notice alleging excess ITC claimed in GSTR-3B vs GSTR-2B by INR 81,000 for tax period November 2023.",
            status="AWAITING_APPROVAL",
            mismatch_amount=Decimal("81000.00"),
            tax_period="2023-11",
            response_deadline=date(2024, 1, 15),
            is_demo=True
        )
        session.add(inv1)

        # Notice for inv1
        notice1 = Notice(
            id=uuid.uuid4(),
            investigation_id=inv1_id,
            notice_number="ZA271223001928K",
            notice_type="DRC-01A",
            gstin="27AABCT1234C1Z5",
            tax_period="2023-11",
            itc_claimed=Decimal("174600.00"),
            itc_available=Decimal("93600.00"),
            itc_mismatch=Decimal("81000.00"),
            response_deadline=date(2024, 1, 15),
            issued_date=date(2023, 12, 28),
            issuing_authority="Deputy Commissioner of State Tax, Circle-5, Mumbai",
            raw_text="FORM GST DRC-01A [See Rule 142(1A)] Intimation of tax ascertained as payable through notice ZA271223001928K. Discrepancy observed: Excess ITC claimed in GSTR-3B compared to GSTR-2B for period 2023-11. Excess ITC: CGST 40500, SGST 40500, Total 81000.",
            extraction_confidence=0.98,
            status="VALIDATED"
        )
        session.add(notice1)

        # Hypotheses for inv1
        hyp1_id = uuid.uuid4()
        hyp1 = Hypothesis(
            id=hyp1_id,
            investigation_id=inv1_id,
            hypothesis_type="TIMING_DIFFERENCE",
            title="Supplier GSTR-1 Filed in Subsequent Tax Period (December 2023)",
            description="Supplier Apex Logistics (27AABCS5555D1Z8) issued invoice INV-2023-0891 on 28-Nov-2023 (Tax INR 81,000) but declared it in their GSTR-1 of December 2023 filed on 11-Jan-2024.",
            status="SUPPORTED",
            confidence_score=0.96,
            supporting_evidence_count=2,
            contradicting_evidence_count=0,
            investigator_rationale="Invoice date 28-Nov-2023 matched with GSTR-2B of Dec 2023. Credit claimed in Nov 2023 strictly based on tax invoice receipt under Sec 16(2).",
            challenge_rationale="Independently confirmed: Apex Logistics filed GSTR-1 on 11-Jan-2024 containing INV-2023-0891. Tax of INR 81,000 duly discharged in their GSTR-3B for Dec 2023. Verified no revenue loss to exchequer."
        )
        session.add(hyp1)

        hyp2_id = uuid.uuid4()
        hyp2 = Hypothesis(
            id=hyp2_id,
            investigation_id=inv1_id,
            hypothesis_type="DUPLICATE_INVOICE",
            title="Potential Duplicate Credit Booking",
            description="Check whether invoice INV-2023-0891 was claimed in multiple periods.",
            status="CONTRADICTED",
            confidence_score=0.92,
            supporting_evidence_count=0,
            contradicting_evidence_count=1,
            investigator_rationale="Ledger scan showed only a single claim in Nov 2023.",
            challenge_rationale="Cross-period ledger reconciliation confirmed zero duplicate claims in FY 2023-24. Finding contradicted and excluded from response."
        )
        session.add(hyp2)

        # Evidence records for inv1
        ev1_id = uuid.uuid4()
        ev1 = EvidenceRecord(
            id=ev1_id,
            investigation_id=inv1_id,
            source_id="INV-2023-0891",
            source_type="INVOICE",
            document_name="Tax Invoice INV-2023-0891 - Apex Logistics",
            amount=Decimal("81000.00"),
            tax_period="2023-11",
            gstin="27AABCS5555D1Z8",
            record_date=datetime(2023, 11, 28, tzinfo=timezone.utc),
            retrieved_at=datetime.now(timezone.utc),
            retrieved_by="Ledger Matcher Agent",
            mcp_server="ledger_mcp",
            status="SUPPORTED",
            verification_notes="Valid tax invoice held with physical delivery challan DC-4412. All Section 16(2) requirements satisfied."
        )
        session.add(ev1)

        ev2_id = uuid.uuid4()
        ev2 = EvidenceRecord(
            id=ev2_id,
            investigation_id=inv1_id,
            source_id="GSTR-2B-2023-12-APEX",
            source_type="GST_RETURN",
            document_name="GSTR-2B Auto-Drafted Return (Dec 2023)",
            amount=Decimal("81000.00"),
            tax_period="2023-12",
            gstin="27AABCS5555D1Z8",
            record_date=datetime(2024, 1, 14, tzinfo=timezone.utc),
            retrieved_at=datetime.now(timezone.utc),
            retrieved_by="Evidence Challenge Engine",
            mcp_server="tax_portal_mcp",
            status="SUPPORTED",
            verification_notes="Appeared in GSTR-2B of Dec 2023 following supplier filing on 11-Jan-2024 with ARN AA271223999912A."
        )
        session.add(ev2)

        session.add(EvidenceLink(hypothesis_id=hyp1_id, evidence_record_id=ev1_id, relationship_type="SUPPORTS", relationship_reason="Original purchase invoice proving possession under Sec 16(2)(a)"))
        session.add(EvidenceLink(hypothesis_id=hyp1_id, evidence_record_id=ev2_id, relationship_type="SUPPORTS", relationship_reason="Subsequent portal reflection confirming supplier compliance and tax discharge"))

        session.add(EvidenceAssessment(
            hypothesis_id=hyp1_id,
            assessed_by="Evidence Challenge Engine",
            assessment_type="EVIDENCE_CHALLENGE",
            result="SUPPORTED",
            rationale="Deterministic matching passed: GSTIN, invoice number, and tax amount identical across invoice, ledger, and subsequent GSTR-2B. No loss of revenue.",
            evidence_gaps="[]"
        ))

        # Report for inv1
        session.add(Report(
            id=uuid.uuid4(),
            investigation_id=inv1_id,
            report_type="RESPONSE_DRAFT",
            title="Reply to DRC-01A Intimation — ZA271223001928K",
            content={
                "notice_number": "ZA271223001928K",
                "gstin": "27AABCT1234C1Z5",
                "tax_period": "2023-11",
                "mismatch_amount": 81000.0,
                "executive_summary": "The alleged discrepancy of INR 81,000 arises purely on account of a timing difference in supplier reporting under GSTR-1, which has since been fully rectified.",
                "verified_findings": [
                    {
                        "finding": "Timing difference on Invoice INV-2023-0891",
                        "supplier": "Apex Logistics (27AABCS5555D1Z8)",
                        "amount": 81000.0,
                        "tax_invoice_date": "2023-11-28",
                        "gstr2b_reflection_period": "2023-12",
                        "statutory_compliance": "Section 16(2) of CGST Act, 2017 fully satisfied; tax discharged to exchequer."
                    }
                ],
                "unresolved_matters": [],
                "statutory_references": ["Section 16(2) CGST Act 2017", "Rule 36(4) CGST Rules 2017", "Circular No. 183/15/2022-GST"],
                "prayer": "In view of the above evidence and subsequent reconciliation in GSTR-2B for December 2023, it is respectfully prayed that the proposed demand of INR 81,000 be dropped."
            },
            is_latest=True,
            generated_by="Response Drafter Agent"
        ))

        # Investigation 2 (In Progress - Supplier Filing Issue)
        inv2_id = uuid.uuid4()
        inv2 = Investigation(
            id=inv2_id,
            organization_id=org_id,
            client_id=client_id,
            created_by_id=accountant_id,
            title="GST DRC-01 ITC Variance Q2 FY 2023-24",
            description="Notice alleging non-reflection of supplier invoices totaling INR 57,600 from Delta Electricals.",
            status="INVESTIGATING",
            mismatch_amount=Decimal("57600.00"),
            tax_period="2023-11",
            response_deadline=date(2024, 2, 28),
            is_demo=True
        )
        session.add(inv2)

        # Investigation 3 (Completed & Approved)
        inv3_id = uuid.uuid4()
        inv3 = Investigation(
            id=inv3_id,
            organization_id=org_id,
            client_id=client_id,
            created_by_id=accountant_id,
            title="GSTR-3A Discrepancy Notice FY 2022-23 (Oct 2022)",
            description="Resolved timing mismatch on capital goods ITC of INR 1,20,000.",
            status="APPROVED",
            mismatch_amount=Decimal("120000.00"),
            tax_period="2022-10",
            response_deadline=date(2023, 11, 30),
            is_demo=True
        )
        session.add(inv3)

        session.add(Approval(
            id=uuid.uuid4(),
            investigation_id=inv3_id,
            reviewer_id=accountant_id,
            action="APPROVE",
            notes="Verified against bank payment proof and chartered engineer certificate. Response filed with range superintendent.",
            is_final=True
        ))

        # Initial Audit Log
        session.add(AuditLog(
            created_at=datetime.now(timezone.utc),
            user_id=owner_id,
            organization_id=org_id,
            action="DATABASE_SEEDED",
            resource_type="SYSTEM",
            resource_id="INITIAL_SEED",
            details={"scenarios_seeded": 12, "demo_clients": 2, "sample_notices": 3}
        ))

        await session.commit()
        logger.info("database_seeding_completed_successfully")

if __name__ == "__main__":
    asyncio.run(seed_data())
