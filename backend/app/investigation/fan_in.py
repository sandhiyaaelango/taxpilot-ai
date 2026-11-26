"""
Fan-in Consolidation Engine — CAT2-057 Phase 2
===============================================
Consolidates parallel per-mismatch investigation results into a single
structured summary consumed by Verification Gate and Response Drafter.

RULES:
- All financial totals use Python arithmetic — never LLM-generated numbers.
- Deduplicates findings by (mismatch_id, invoice_ref) pair.
- Preserves SUPPORTED, CONTRADICTED, and UNVERIFIED findings separately.
- Missing evidence is explicitly listed — never silently dropped.
"""

from typing import Dict, Any, List
from app.config.logging import get_logger

logger = get_logger("fan_in")


def consolidate_mismatch_results(mismatch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Consolidate per-mismatch investigation results into a single fan-in summary.

    Financial arithmetic is performed in Python using float accumulation with
    rounding to 2 decimal places.  LLMs are never used for financial totals.

    Deduplication key: (mismatch_id, invoice_ref) — prevents double-counting
    if the same invoice appears in multiple mismatch records.

    Args:
        mismatch_results: List of mismatch_item dicts returned by fan_out_mismatches().

    Returns:
        Dict with:
            supported_findings       — findings where status == SUPPORTED
            contradicted_findings    — findings where status == CONTRADICTED
            unverified_findings      — findings where status == UNVERIFIED
            failed_mismatches        — items that raised errors during investigation
            total_mismatch_amount    — Python sum of all mismatch_amounts (float)
            total_supported_amount   — sum for SUPPORTED items only
            total_unverified_amount  — sum for UNVERIFIED items only
            total_failed_amount      — sum for FAILED items (conservative: counted as risk)
            unique_evidence_ids      — deduplicated list of all evidence IDs
            missing_evidence_summary — human-readable list of unverified/missing items
            classification_counts    — {TIMING_DIFFERENCE: N, ...}
            mismatch_count           — total number of mismatches processed
    """
    supported_findings: List[Dict[str, Any]] = []
    contradicted_findings: List[Dict[str, Any]] = []
    unverified_findings: List[Dict[str, Any]] = []
    failed_mismatches: List[Dict[str, Any]] = []

    total_mismatch_amount: float = 0.0
    total_supported_amount: float = 0.0
    total_unverified_amount: float = 0.0
    total_failed_amount: float = 0.0

    all_evidence_ids: List[str] = []
    missing_evidence_summary: List[str] = []
    classification_counts: Dict[str, int] = {}

    # Deduplication set: (mismatch_id, invoice_ref) prevents double-counting
    seen_keys = set()

    for item in mismatch_results:
        mismatch_id = item.get("mismatch_id", "UNKNOWN")
        invoice_ref = item.get("invoice_ref", "")
        dedup_key = (mismatch_id, invoice_ref)

        if dedup_key in seen_keys:
            logger.warning("fan_in_dedup_skip", mismatch_id=mismatch_id, invoice_ref=invoice_ref)
            continue
        seen_keys.add(dedup_key)

        # Accumulate totals in Python arithmetic
        amt = float(item.get("mismatch_amount") or 0.0)
        total_mismatch_amount += amt

        status = item.get("status", "UNVERIFIED")
        classification = item.get("classification", "UNCLASSIFIED")
        classification_counts[classification] = classification_counts.get(classification, 0) + 1

        # Collect all evidence IDs
        for eid in item.get("evidence_ids", []):
            if eid and eid not in all_evidence_ids:
                all_evidence_ids.append(eid)

        base_finding = {
            "mismatch_id": mismatch_id,
            "invoice_ref": invoice_ref,
            "mismatch_amount": amt,
            "classification": classification,
            "tax_period": item.get("tax_period", ""),
            "gstin": item.get("gstin", ""),
            "evidence_ids": item.get("evidence_ids", []),
            "findings": item.get("findings", []),
            "react_steps": item.get("react_steps", 0),
        }

        if status == "SUPPORTED":
            total_supported_amount += amt
            supported_findings.append(base_finding)

        elif status == "CONTRADICTED":
            contradicted_findings.append({**base_finding, "contradiction_reason": item.get("error", "")})

        elif status == "FAILED":
            total_failed_amount += amt
            failed_mismatches.append({**base_finding, "error": item.get("error", "Unknown error")})
            missing_evidence_summary.append(
                f"[{mismatch_id}] Investigation FAILED for invoice {invoice_ref}: {item.get('error', 'unknown')}"
            )

        else:  # UNVERIFIED or anything else
            total_unverified_amount += amt
            unverified_findings.append(base_finding)
            missing_evidence_summary.append(
                f"[{mismatch_id}] Invoice {invoice_ref} — evidence unverified "
                f"(classification: {classification}, amount: INR {amt:.2f})"
            )

    # Round all financial totals to 2 decimal places (Python arithmetic)
    summary = {
        "supported_findings": supported_findings,
        "contradicted_findings": contradicted_findings,
        "unverified_findings": unverified_findings,
        "failed_mismatches": failed_mismatches,
        "total_mismatch_amount": round(total_mismatch_amount, 2),
        "total_supported_amount": round(total_supported_amount, 2),
        "total_unverified_amount": round(total_unverified_amount, 2),
        "total_failed_amount": round(total_failed_amount, 2),
        "unique_evidence_ids": all_evidence_ids,
        "missing_evidence_summary": missing_evidence_summary,
        "classification_counts": classification_counts,
        "mismatch_count": len(mismatch_results),
        "supported_count": len(supported_findings),
        "contradicted_count": len(contradicted_findings),
        "unverified_count": len(unverified_findings),
        "failed_count": len(failed_mismatches),
    }

    logger.info(
        "fan_in_consolidation_complete",
        mismatch_count=summary["mismatch_count"],
        supported=summary["supported_count"],
        unverified=summary["unverified_count"],
        failed=summary["failed_count"],
        total_mismatch_amount=summary["total_mismatch_amount"],
        total_supported_amount=summary["total_supported_amount"],
    )

    return summary
