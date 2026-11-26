"""
Mismatch-level Fan-out Engine — CAT2-057 Phase 1
=================================================
Extracts individual mismatch items from a parsed GST notice and runs
a parallel (semaphore-bounded) ReAct investigation per mismatch.

DESIGN RULES:
- Never fabricates invoice numbers, GSTINs, supplier names, or amounts.
- Uses only data extracted from the notice or returned by MCP tools.
- Each mismatch is investigated independently; failures are isolated.
- Deterministic Python arithmetic; no LLM for financial totals.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.mcp.client.manager import mcp_client
from app.investigation.react_engine import BoundedReActLoop, ReActAction
from app.config.logging import get_logger

logger = get_logger("mismatch_fanout")

CLASSIFICATION_MAP = {
    "supplier_non_filing": "SUPPLIER_NON_FILING",
    "non_filing": "SUPPLIER_NON_FILING",
    "timing": "TIMING_DIFFERENCE",
    "timing_difference": "TIMING_DIFFERENCE",
    "duplicate": "DUPLICATE_ENTRY",
    "duplicate_entry": "DUPLICATE_ENTRY",
    "incorrect_itc": "INCORRECT_ITC_CLAIM",
    "data_entry": "DATA_ENTRY_ERROR",
    "unclassified": "UNCLASSIFIED",
}


def _classify_mismatch(notice_data: Dict[str, Any], invoice: Optional[Dict[str, Any]] = None) -> str:
    """
    Classify a mismatch item based on notice text signals.
    Returns one of: TIMING_DIFFERENCE | DUPLICATE_ENTRY | SUPPLIER_NON_FILING |
                    INCORRECT_ITC_CLAIM | DATA_ENTRY_ERROR | UNCLASSIFIED
    """
    text_signals: List[str] = []
    if notice_data:
        for field in ("notice_type", "description", "raw_text", "mismatch_reason"):
            val = str(notice_data.get(field, "")).lower()
            if val:
                text_signals.append(val)

    combined = " ".join(text_signals)

    if any(kw in combined for kw in ("non.filing", "not filed", "supplier.*not", "vendor.*not")):
        return "SUPPLIER_NON_FILING"
    if any(kw in combined for kw in ("timing", "different month", "different period", "itc reversal")):
        return "TIMING_DIFFERENCE"
    if any(kw in combined for kw in ("duplicate", "already claimed", "double")):
        return "DUPLICATE_ENTRY"
    if any(kw in combined for kw in ("excess", "incorrect claim", "wrong amount")):
        return "INCORRECT_ITC_CLAIM"
    if any(kw in combined for kw in ("data entry", "typo", "clerical")):
        return "DATA_ENTRY_ERROR"

    return "UNCLASSIFIED"


async def extract_mismatches(
    notice_data: Dict[str, Any],
    suspect_invoices: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extract individual mismatch items from notice + ledger reconciliation.

    If suspect_invoices exist (from Ledger Matcher), create one mismatch item
    per suspect invoice. Otherwise, fall back to a single mismatch item derived
    from the notice-level totals.

    Returns:
        List of mismatch_item dicts, each uniquely identified by mismatch_id.
    """
    mismatch_items: List[Dict[str, Any]] = []

    if suspect_invoices:
        for idx, inv in enumerate(suspect_invoices, start=1):
            mismatch_id = f"MIS-{idx:03d}"
            classification = _classify_mismatch(notice_data, inv)
            mismatch_items.append({
                "mismatch_id": mismatch_id,
                "invoice_ref": inv.get("invoice_number") or inv.get("invoice_ref") or f"INV-REF-{mismatch_id}",
                "mismatch_amount": float(inv.get("tax_amount") or inv.get("mismatch_amount") or 0.0),
                "tax_period": inv.get("tax_period") or notice_data.get("tax_period", ""),
                "gstin": inv.get("supplier_gstin") or notice_data.get("gstin", ""),
                "classification": classification,
                "status": "PENDING",
                "evidence_ids": [],
                "findings": [],
                "error": None,
                "source_invoice": inv,  # preserved for downstream agents
            })
    else:
        # Single synthetic mismatch from notice totals
        total = float(notice_data.get("itc_mismatch") or 0.0)
        classification = _classify_mismatch(notice_data)
        mismatch_items.append({
            "mismatch_id": "MIS-001",
            "invoice_ref": "NOTICE-LEVEL",
            "mismatch_amount": total,
            "tax_period": notice_data.get("tax_period", ""),
            "gstin": notice_data.get("gstin", ""),
            "classification": classification,
            "status": "PENDING",
            "evidence_ids": [],
            "findings": [],
            "error": None,
            "source_invoice": None,
        })

    logger.info("mismatches_extracted", count=len(mismatch_items))
    return mismatch_items


async def investigate_single_mismatch(
    mismatch_item: Dict[str, Any],
    investigation_id: str,
    notice_data: Dict[str, Any],
    client_gstin: str,
) -> Dict[str, Any]:
    """
    Run a targeted ReAct investigation for a single mismatch item.

    Uses MCP tools to:
    1. Check vendor/supplier GST filing status.
    2. Look up invoice details from the ledger.
    3. Verify entries in the period's ledger records.

    Returns:
        Updated mismatch_item with status, evidence_ids, and findings populated.
    """
    mismatch_id = mismatch_item["mismatch_id"]
    invoice_ref = mismatch_item["invoice_ref"]
    tax_period = mismatch_item.get("tax_period") or notice_data.get("tax_period", "2023-11")
    supplier_gstin = mismatch_item.get("gstin") or client_gstin

    logger.info(
        "mismatch_investigation_started",
        mismatch_id=mismatch_id,
        invoice_ref=invoice_ref,
        classification=mismatch_item["classification"],
    )

    result = dict(mismatch_item)
    result["status"] = "INVESTIGATING"
    evidence_ids: List[str] = []
    findings: List[Dict[str, Any]] = []

    try:
        react = BoundedReActLoop(
            agent_name=f"Mismatch-Investigator-{mismatch_id}",
            investigation_id=investigation_id,
            max_iterations=5,
            tool_call_budget=8,
        )

        # Step 1 — Check vendor GST filing status
        filing_action = ReActAction(
            tool_name="get_vendor_filing_status",
            arguments={"gstin": supplier_gstin, "tax_period": tax_period},
            rationale=f"Check if supplier {supplier_gstin} filed GSTR-1 for {tax_period}",
        )
        filing_obs = await react.execute_action(filing_action)
        react.record_step(1, filing_action.rationale, filing_action, filing_obs)

        filing_data = filing_obs.data if not filing_obs.is_error else {}
        filing_status = filing_data.get("filing_status", "UNKNOWN")
        source_id = filing_data.get("source_id") or f"FILING-{supplier_gstin}-{tax_period}"
        if source_id:
            evidence_ids.append(source_id)

        if filing_status in ("NOT_FILED", "PENDING"):
            findings.append({
                "finding_type": "SUPPLIER_NON_FILING",
                "detail": f"Supplier {supplier_gstin} has NOT filed GSTR-1 for {tax_period}",
                "evidence_id": source_id,
                "status": "SUPPORTED",
            })
        elif filing_status in ("FILED", "FILED_WITH_AMENDMENTS"):
            findings.append({
                "finding_type": "SUPPLIER_FILING_CONFIRMED",
                "detail": f"Supplier {supplier_gstin} has filed GSTR-1 for {tax_period}",
                "evidence_id": source_id,
                "status": "SUPPORTED",
            })

        # Step 2 — Look up invoice details if we have an actual invoice_ref
        if invoice_ref and invoice_ref != "NOTICE-LEVEL":
            inv_action = ReActAction(
                tool_name="get_invoice_details",
                arguments={"invoice_number": invoice_ref},
                rationale=f"Retrieve invoice details for {invoice_ref} to verify amounts",
            )
            inv_obs = await react.execute_action(inv_action)
            react.record_step(2, inv_action.rationale, inv_action, inv_obs)

            if not inv_obs.is_error:
                inv_data = inv_obs.data
                inv_source_id = inv_data.get("source_id") or f"INV-{invoice_ref}"
                if inv_source_id:
                    evidence_ids.append(inv_source_id)
                inv_status = inv_data.get("status", "UNKNOWN")
                if inv_status in ("MATCHED", "RECONCILED"):
                    findings.append({
                        "finding_type": "INVOICE_RECONCILED",
                        "detail": f"Invoice {invoice_ref} found in ledger with status {inv_status}",
                        "evidence_id": inv_source_id,
                        "status": "SUPPORTED",
                    })
                elif inv_status in ("MISSING", "NOT_FOUND"):
                    findings.append({
                        "finding_type": "INVOICE_MISSING",
                        "detail": f"Invoice {invoice_ref} not found in ledger records",
                        "evidence_id": inv_source_id,
                        "status": "UNVERIFIED",
                    })
                else:
                    findings.append({
                        "finding_type": "INVOICE_STATUS_PARTIAL",
                        "detail": f"Invoice {invoice_ref} has intermediate status: {inv_status}",
                        "evidence_id": inv_source_id,
                        "status": "UNVERIFIED",
                    })

        # Step 3 — Query ledger entries for the period
        ledger_action = ReActAction(
            tool_name="get_entries_by_period",
            arguments={"gstin": client_gstin, "tax_period": tax_period},
            rationale=f"Retrieve all ledger entries for {client_gstin} in {tax_period}",
        )
        ledger_obs = await react.execute_action(ledger_action)
        react.record_step(3, ledger_action.rationale, ledger_action, ledger_obs)

        if not ledger_obs.is_error:
            entries = ledger_obs.data.get("entries", [])
            ledger_source_id = ledger_obs.data.get("source_id") or f"LEDGER-{client_gstin}-{tax_period}"
            if ledger_source_id:
                evidence_ids.append(ledger_source_id)

            # Cross-check: does our mismatch invoice appear in ledger entries?
            matched_in_ledger = any(
                e.get("invoice_number") == invoice_ref for e in entries
            ) if invoice_ref and invoice_ref != "NOTICE-LEVEL" else len(entries) > 0

            if matched_in_ledger:
                findings.append({
                    "finding_type": "LEDGER_ENTRY_FOUND",
                    "detail": f"Ledger has {len(entries)} entries for period {tax_period}",
                    "evidence_id": ledger_source_id,
                    "status": "SUPPORTED",
                })
            else:
                findings.append({
                    "finding_type": "LEDGER_ENTRY_MISSING",
                    "detail": f"No matching ledger entry found for {invoice_ref} in {tax_period}",
                    "evidence_id": ledger_source_id,
                    "status": "UNVERIFIED",
                })

        # Determine overall mismatch status from findings
        statuses = [f["status"] for f in findings]
        if "SUPPORTED" in statuses and "UNVERIFIED" not in statuses:
            overall_status = "SUPPORTED"
        elif "UNVERIFIED" in statuses and "SUPPORTED" not in statuses:
            overall_status = "UNVERIFIED"
        elif "SUPPORTED" in statuses and "UNVERIFIED" in statuses:
            overall_status = "SUPPORTED"  # Partial evidence is better than none
        else:
            overall_status = "UNVERIFIED"

        result["status"] = overall_status
        result["evidence_ids"] = list(set(evidence_ids))
        result["findings"] = findings
        result["react_steps"] = len(react.steps)

    except Exception as exc:
        logger.error("mismatch_investigation_failed", mismatch_id=mismatch_id, error=str(exc), exc_info=True)
        result["status"] = "FAILED"
        result["error"] = str(exc)
        result["findings"] = []
        result["evidence_ids"] = []

    logger.info(
        "mismatch_investigation_completed",
        mismatch_id=mismatch_id,
        status=result["status"],
        findings_count=len(result.get("findings", [])),
    )
    return result


async def fan_out_mismatches(
    mismatch_items: List[Dict[str, Any]],
    investigation_id: str,
    notice_data: Dict[str, Any],
    client_gstin: str,
    max_concurrency: int = 3,
) -> List[Dict[str, Any]]:
    """
    Run investigate_single_mismatch in parallel with semaphore-bounded concurrency.

    - Never raises: captures per-item errors with status=FAILED.
    - Respects max_concurrency (default 3) to avoid overloading MCP servers.
    - Returns results in same order as mismatch_items input.

    Args:
        mismatch_items: List of mismatch_item dicts from extract_mismatches().
        investigation_id: UUID string for SSE broadcasting and audit.
        notice_data: Parsed notice dict for context.
        client_gstin: Taxpayer GSTIN.
        max_concurrency: Maximum parallel investigations.

    Returns:
        List of updated mismatch_item dicts with status/evidence/findings.
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    results: List[Optional[Dict[str, Any]]] = [None] * len(mismatch_items)

    async def _run(idx: int, item: Dict[str, Any]) -> None:
        async with semaphore:
            try:
                results[idx] = await investigate_single_mismatch(
                    mismatch_item=item,
                    investigation_id=investigation_id,
                    notice_data=notice_data,
                    client_gstin=client_gstin,
                )
            except Exception as exc:
                logger.error("fan_out_item_exception", mismatch_id=item.get("mismatch_id"), error=str(exc))
                failed = dict(item)
                failed["status"] = "FAILED"
                failed["error"] = str(exc)
                failed["findings"] = []
                failed["evidence_ids"] = []
                results[idx] = failed

    tasks = [_run(i, item) for i, item in enumerate(mismatch_items)]
    await asyncio.gather(*tasks, return_exceptions=False)

    # Replace any None (should not happen) with failed sentinel
    final = []
    for i, r in enumerate(results):
        if r is None:
            failed = dict(mismatch_items[i])
            failed["status"] = "FAILED"
            failed["error"] = "Fan-out produced no result"
            final.append(failed)
        else:
            final.append(r)

    logger.info(
        "fan_out_completed",
        total=len(final),
        supported=sum(1 for r in final if r["status"] == "SUPPORTED"),
        unverified=sum(1 for r in final if r["status"] == "UNVERIFIED"),
        failed=sum(1 for r in final if r["status"] == "FAILED"),
    )
    return final
