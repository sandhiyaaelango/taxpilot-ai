import uuid
import time
import json
from datetime import datetime, timezone, date
from typing import Dict, Any, List, Optional
from decimal import Decimal

from app.workflows.state import InvestigationWorkflowState
from app.agents.notice_parser import NoticeParserAgent
from app.agents.ledger_matcher import LedgerMatcherAgent
from app.agents.root_cause_investigator import RootCauseInvestigatorAgent
from app.agents.evidence_challenge import EvidenceChallengeEngine
from app.investigation.verification_gate import verification_gate
from app.investigation.mismatch_fanout import extract_mismatches, fan_out_mismatches
from app.investigation.fan_in import consolidate_mismatch_results
from app.agents.response_drafter import ResponseDrafterAgent
from app.investigation.stream_manager import stream_manager
from app.database.session import AsyncSessionLocal
from app.database.models.agent import AgentRun, ToolCall
from app.config.logging import get_logger


def _compute_deadline_urgency(deadline_str: Optional[str]) -> Dict[str, Any]:
    """Compute deadline urgency fields from YYYY-MM-DD string. Pure Python, no LLM."""
    if not deadline_str:
        return {"response_deadline": None, "deadline_days_remaining": None, "is_overdue": False, "deadline_urgency": "NONE"}
    try:
        deadline_date = date.fromisoformat(deadline_str[:10])
        today = date.today()
        days_remaining = (deadline_date - today).days
        is_overdue = days_remaining < 0
        if is_overdue:
            urgency = "CRITICAL"
        elif days_remaining < 3:
            urgency = "CRITICAL"
        elif days_remaining < 7:
            urgency = "HIGH"
        elif days_remaining < 14:
            urgency = "MEDIUM"
        else:
            urgency = "LOW"
        return {
            "response_deadline": deadline_str,
            "deadline_days_remaining": days_remaining,
            "is_overdue": is_overdue,
            "deadline_urgency": urgency,
        }
    except Exception:
        return {"response_deadline": deadline_str, "deadline_days_remaining": None, "is_overdue": False, "deadline_urgency": "NONE"}

logger = get_logger("workflow_nodes")


# Instantiate agent singletons
notice_parser_agent = NoticeParserAgent()
ledger_matcher_agent = LedgerMatcherAgent()
root_cause_agent = RootCauseInvestigatorAgent()
evidence_challenge_engine = EvidenceChallengeEngine()
response_drafter_agent = ResponseDrafterAgent()

async def _save_agent_run(
    investigation_id: str,
    agent_name: str,
    status: str,
    started_at: datetime,
    completed_at: Optional[datetime],
    duration_ms: int,
    task_desc: str,
    output_summary: str,
    steps: Optional[List[Any]] = None,
    error_message: Optional[str] = None
) -> Optional[uuid.UUID]:
    """Helper to persist AgentRun and associated ToolCall records into database."""
    try:
        inv_uuid = uuid.UUID(investigation_id) if isinstance(investigation_id, str) and len(investigation_id) == 36 else None
        if not inv_uuid:
            return None

        async with AsyncSessionLocal() as session:
            run_id = uuid.uuid4()
            tool_calls_count = len(steps) if steps else 0
            
            agent_run = AgentRun(
                id=run_id,
                investigation_id=inv_uuid,
                agent_name=agent_name,
                status=status,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                input_tokens=150 + tool_calls_count * 80,
                output_tokens=120 + tool_calls_count * 60,
                estimated_cost_usd=Decimal(str(round(0.00015 * (tool_calls_count + 1), 6))),
                retry_count=0,
                error_message=error_message,
                agent_metadata={"task": task_desc, "summary": output_summary}
            )
            session.add(agent_run)

            # Record Tool Calls if available
            if steps:
                for step in steps:
                    action = step.action
                    obs = step.observation
                    mcp_server = "Ledger MCP Server" if any(k in action.tool_name.lower() for k in ["invoice", "ledger", "entries"]) else "Tax Portal MCP Server"
                    
                    tc = ToolCall(
                        id=uuid.uuid4(),
                        agent_run_id=run_id,
                        tool_name=action.tool_name,
                        mcp_server=mcp_server,
                        arguments=action.arguments,
                        result_summary=obs.result_summary,
                        result_status="ERROR" if obs.is_error else "SUCCESS",
                        duration_ms=obs.duration_ms,
                        retry_count=0,
                        error_message=obs.data.get("error") if obs.is_error else None,
                        called_at=datetime.now(timezone.utc)
                    )
                    session.add(tc)

            await session.commit()
            return run_id
    except Exception as e:
        logger.warning("failed_to_persist_agent_run", agent=agent_name, error=str(e))
        return None

async def node_load_investigation(state: InvestigationWorkflowState) -> InvestigationWorkflowState:
    inv_id = state.get("investigation_id", "")
    logger.info("node_load_investigation", inv_id=inv_id)
    state["current_node"] = "LOAD_INVESTIGATION"
    state.setdefault("step_history", []).append("LOAD_INVESTIGATION")

    await stream_manager.broadcast(inv_id, "node_transition", {"node": "LOAD_INVESTIGATION"})
    
    # Broadcast Supervisor Agent Start
    started_at = datetime.now(timezone.utc)
    task_desc = "Initializing investigation workflow and loading client profile"
    await stream_manager.broadcast(inv_id, "agent_started", {
        "agent_name": "Supervisor Agent",
        "status": "RUNNING",
        "task": task_desc,
        "started_at": started_at.isoformat()
    })

    summary = f"Client {state.get('client_name', 'Client')} loaded with GSTIN {state.get('client_gstin', '')}"
    await _save_agent_run(
        investigation_id=inv_id,
        agent_name="Supervisor Agent",
        status="COMPLETED",
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        duration_ms=45,
        task_desc=task_desc,
        output_summary=summary
    )

    await stream_manager.broadcast(inv_id, "agent_completed", {
        "agent_name": "Supervisor Agent",
        "status": "COMPLETED",
        "duration_ms": 45,
        "output_summary": summary
    })
    return state

async def node_parse_notice(state: InvestigationWorkflowState) -> InvestigationWorkflowState:
    inv_id = state.get("investigation_id", "")
    logger.info("node_parse_notice", inv_id=inv_id)
    state["current_node"] = "PARSE_NOTICE"
    state["step_history"].append("PARSE_NOTICE")

    await stream_manager.broadcast(inv_id, "node_transition", {"node": "PARSE_NOTICE"})
    
    started_at = datetime.now(timezone.utc)
    t0 = time.time()
    task_desc = "Extracting structured metadata, GSTIN, tax period, and ITC amounts"
    await stream_manager.broadcast(inv_id, "agent_started", {
        "agent_name": "Notice Parser Agent",
        "status": "RUNNING",
        "task": task_desc,
        "started_at": started_at.isoformat()
    })

    text = state.get("notice_text", "")
    parsed = await notice_parser_agent.parse_text(text)
    state["notice_data"] = parsed.model_dump()

    # Phase 3: Extract deadline and compute urgency fields right after parse
    deadline_str = parsed.response_deadline or state.get("notice_data", {}).get("response_deadline")
    urgency_info = _compute_deadline_urgency(deadline_str)
    state.update(urgency_info)

    duration_ms = int((time.time() - t0) * 1000)
    summary = f"Parsed Notice {parsed.notice_number or parsed.notice_type} (GSTIN: {parsed.gstin}, Mismatch: INR {parsed.itc_mismatch})"

    await _save_agent_run(
        investigation_id=inv_id,
        agent_name="Notice Parser Agent",
        status="COMPLETED",
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        duration_ms=duration_ms,
        task_desc=task_desc,
        output_summary=summary
    )

    await stream_manager.broadcast(inv_id, "agent_completed", {
        "agent_name": "Notice Parser Agent",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "output_summary": summary,
        "notice_data": state["notice_data"]
    })

    return state

async def node_validate_notice(state: InvestigationWorkflowState) -> InvestigationWorkflowState:
    inv_id = state.get("investigation_id", "")
    logger.info("node_validate_notice", inv_id=inv_id)
    state["current_node"] = "VALIDATE_NOTICE"
    state["step_history"].append("VALIDATE_NOTICE")
    
    notice = state.get("notice_data", {})
    errors = []
    if not notice.get("gstin"):
        errors.append("Missing GSTIN in notice")
    if not notice.get("tax_period"):
        errors.append("Missing tax period in notice")
    if notice.get("itc_mismatch") is None:
        errors.append("Missing ITC mismatch amount in notice")

    state["notice_valid"] = len(errors) == 0
    state["notice_validation_errors"] = errors

    await stream_manager.broadcast(inv_id, "notice_validation_evaluated", {
        "notice_valid": state["notice_valid"],
        "errors": errors
    })
    return state

async def node_build_investigation_plan(state: InvestigationWorkflowState) -> InvestigationWorkflowState:
    inv_id = state.get("investigation_id", "")
    logger.info("node_build_investigation_plan")
    state["current_node"] = "BUILD_INVESTIGATION_PLAN"
    state["step_history"].append("BUILD_INVESTIGATION_PLAN")
    
    notice = state.get("notice_data", {})
    state["investigation_plan"] = {
        "plan_id": f"PLAN-{uuid.uuid4().hex[:8]}",
        "mismatch_amount": notice.get("itc_mismatch", 0.0),
        "target_period": notice.get("tax_period"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await stream_manager.broadcast(inv_id, "plan_created", {
        "investigation_plan": state["investigation_plan"]
    })
    return state

async def node_create_invoice_tasks(state: InvestigationWorkflowState) -> InvestigationWorkflowState:
    inv_id = state.get("investigation_id", "")
    logger.info("node_create_invoice_tasks")
    state["current_node"] = "CREATE_INVOICE_TASKS"
    state["step_history"].append("CREATE_INVOICE_TASKS")
    
    notice = state.get("notice_data", {})
    state["invoice_tasks"] = [
        {
            "task_id": f"TSK-INV-RECON-{uuid.uuid4().hex[:6]}",
            "type": "RECONCILE_INVOICE_LEDGER",
            "amount": notice.get("itc_mismatch", 0.0)
        }
    ]

    # Phase 1: Extract individual mismatch items from notice + suspect invoices (may be empty here)
    suspect_invoices = state.get("suspect_invoices", [])
    mismatch_items = await extract_mismatches(
        notice_data=notice,
        suspect_invoices=suspect_invoices,
    )
    state["mismatch_items"] = mismatch_items

    await stream_manager.broadcast(inv_id, "mismatch_items_extracted", {
        "mismatch_count": len(mismatch_items),
        "mismatches": [
            {
                "mismatch_id": m["mismatch_id"],
                "invoice_ref": m["invoice_ref"],
                "mismatch_amount": m["mismatch_amount"],
                "classification": m["classification"],
                "status": m["status"],
            }
            for m in mismatch_items
        ]
    })
    return state

async def node_ledger_investigation(state: InvestigationWorkflowState) -> InvestigationWorkflowState:
    inv_id = state.get("investigation_id", "INV-UNKNOWN")
    logger.info("node_ledger_investigation", inv_id=inv_id)
    state["current_node"] = "LEDGER_INVESTIGATION"
    state["step_history"].append("LEDGER_INVESTIGATION")

    await stream_manager.broadcast(inv_id, "node_transition", {"node": "LEDGER_INVESTIGATION"})

    started_at = datetime.now(timezone.utc)
    t0 = time.time()
    task_desc = "Executing ReAct Loop 1: Querying Ledger MCP server to reconcile invoices and entries"
    await stream_manager.broadcast(inv_id, "agent_started", {
        "agent_name": "Ledger Matcher Agent",
        "status": "RUNNING",
        "task": task_desc,
        "started_at": started_at.isoformat()
    })

    notice = state.get("notice_data", {})
    client_gstin = notice.get("gstin") or state.get("client_gstin", "27AABCT1234C1Z5")
    tax_period = notice.get("tax_period", "2023-11")
    mismatch_amt = notice.get("itc_mismatch", 81000.0)

    log = await ledger_matcher_agent.investigate_ledger(
        investigation_id=inv_id,
        client_gstin=client_gstin,
        tax_period=tax_period,
        mismatch_amount=mismatch_amt
    )
    state["suspect_invoices"] = log.final_data.get("matched_invoices", [])

    duration_ms = int((time.time() - t0) * 1000)
    matched_count = len(state["suspect_invoices"])
    summary = f"Reconciled ledger records. Identified {matched_count} matching invoice(s) across {log.total_iterations} ReAct iterations."

    await _save_agent_run(
        investigation_id=inv_id,
        agent_name="Ledger Matcher Agent",
        status="COMPLETED",
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        duration_ms=duration_ms,
        task_desc=task_desc,
        output_summary=summary,
        steps=log.steps
    )

    await stream_manager.broadcast(inv_id, "agent_completed", {
        "agent_name": "Ledger Matcher Agent",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "output_summary": summary,
        "tool_calls_count": log.tool_calls_count,
        "matched_invoices_count": matched_count
    })

    # Phase 1: Extract individual mismatch items now that suspect_invoices are populated
    notice = state.get("notice_data", {})
    mismatch_items = await extract_mismatches(
        notice_data=notice,
        suspect_invoices=state["suspect_invoices"],
    )
    state["mismatch_items"] = mismatch_items

    await stream_manager.broadcast(inv_id, "mismatch_items_extracted", {
        "mismatch_count": len(mismatch_items),
        "mismatches": [
            {
                "mismatch_id": m["mismatch_id"],
                "invoice_ref": m["invoice_ref"],
                "mismatch_amount": m["mismatch_amount"],
                "classification": m["classification"],
                "status": m["status"],
            }
            for m in mismatch_items
        ]
    })

    return state


async def node_mismatch_fanout(state: InvestigationWorkflowState) -> InvestigationWorkflowState:
    """Phase 1 Fan-out: Investigate each mismatch item in parallel."""
    inv_id = state.get("investigation_id", "INV-UNKNOWN")
    logger.info("node_mismatch_fanout", inv_id=inv_id)
    state["current_node"] = "MISMATCH_FANOUT"
    state["step_history"].append("MISMATCH_FANOUT")

    await stream_manager.broadcast(inv_id, "node_transition", {"node": "MISMATCH_FANOUT"})

    started_at = datetime.now(timezone.utc)
    t0 = time.time()
    mismatch_items = state.get("mismatch_items", [])
    notice = state.get("notice_data", {})
    client_gstin = notice.get("gstin") or state.get("client_gstin", "27AABCT1234C1Z5")

    await stream_manager.broadcast(inv_id, "agent_started", {
        "agent_name": "Mismatch Fan-out Engine",
        "status": "RUNNING",
        "task": f"Parallel investigation of {len(mismatch_items)} individual mismatch(es)",
        "started_at": started_at.isoformat()
    })

    mismatch_results = await fan_out_mismatches(
        mismatch_items=mismatch_items,
        investigation_id=inv_id,
        notice_data=notice,
        client_gstin=client_gstin,
        max_concurrency=3,
    )
    state["mismatch_results"] = mismatch_results

    duration_ms = int((time.time() - t0) * 1000)
    supported = sum(1 for r in mismatch_results if r["status"] == "SUPPORTED")
    unverified = sum(1 for r in mismatch_results if r["status"] == "UNVERIFIED")
    summary = (
        f"Fan-out complete: {len(mismatch_results)} mismatches investigated. "
        f"{supported} SUPPORTED, {unverified} UNVERIFIED."
    )

    await _save_agent_run(
        investigation_id=inv_id,
        agent_name="Mismatch Fan-out Engine",
        status="COMPLETED",
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        duration_ms=duration_ms,
        task_desc="Per-mismatch parallel investigation",
        output_summary=summary
    )

    await stream_manager.broadcast(inv_id, "agent_completed", {
        "agent_name": "Mismatch Fan-out Engine",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "output_summary": summary,
        "mismatch_results": [
            {"mismatch_id": r["mismatch_id"], "status": r["status"], "classification": r["classification"]}
            for r in mismatch_results
        ]
    })

    return state


async def node_fan_in(state: InvestigationWorkflowState) -> InvestigationWorkflowState:
    """Phase 2 Fan-in: Consolidate parallel mismatch results."""
    inv_id = state.get("investigation_id", "INV-UNKNOWN")
    logger.info("node_fan_in", inv_id=inv_id)
    state["current_node"] = "FAN_IN"
    state["step_history"].append("FAN_IN")

    await stream_manager.broadcast(inv_id, "node_transition", {"node": "FAN_IN"})

    started_at = datetime.now(timezone.utc)
    t0 = time.time()

    mismatch_results = state.get("mismatch_results", [])
    fan_in_summary = consolidate_mismatch_results(mismatch_results)
    state["fan_in_summary"] = fan_in_summary

    duration_ms = int((time.time() - t0) * 1000)
    summary = (
        f"Fan-in consolidated {fan_in_summary['mismatch_count']} mismatches. "
        f"Total mismatch: INR {fan_in_summary['total_mismatch_amount']:.2f}, "
        f"Supported: INR {fan_in_summary['total_supported_amount']:.2f}."
    )

    await _save_agent_run(
        investigation_id=inv_id,
        agent_name="Fan-in Consolidator",
        status="COMPLETED",
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        duration_ms=duration_ms,
        task_desc="Consolidate per-mismatch results into unified summary",
        output_summary=summary
    )

    await stream_manager.broadcast(inv_id, "agent_completed", {
        "agent_name": "Fan-in Consolidator",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "output_summary": summary,
        "fan_in_summary": {
            "total_mismatch_amount": fan_in_summary["total_mismatch_amount"],
            "total_supported_amount": fan_in_summary["total_supported_amount"],
            "total_unverified_amount": fan_in_summary["total_unverified_amount"],
            "supported_count": fan_in_summary["supported_count"],
            "unverified_count": fan_in_summary["unverified_count"],
        }
    })

    return state

async def node_root_cause_investigation(state: InvestigationWorkflowState) -> InvestigationWorkflowState:
    inv_id = state.get("investigation_id", "INV-UNKNOWN")
    logger.info("node_root_cause_investigation", inv_id=inv_id)
    state["current_node"] = "ROOT_CAUSE_INVESTIGATION"
    state["step_history"].append("ROOT_CAUSE_INVESTIGATION")

    await stream_manager.broadcast(inv_id, "node_transition", {"node": "ROOT_CAUSE_INVESTIGATION"})

    started_at = datetime.now(timezone.utc)
    t0 = time.time()
    task_desc = "Executing ReAct Loop 2: Checking Tax Portal MCP for vendor returns and formulating hypotheses"
    await stream_manager.broadcast(inv_id, "agent_started", {
        "agent_name": "Root-Cause Investigator",
        "status": "RUNNING",
        "task": task_desc,
        "started_at": started_at.isoformat()
    })

    notice = state.get("notice_data", {})
    client_gstin = notice.get("gstin") or state.get("client_gstin", "27AABCT1234C1Z5")
    tax_period = notice.get("tax_period", "2023-11")
    mismatch_amt = notice.get("itc_mismatch", 81000.0)
    suspect_invoices = state.get("suspect_invoices", [])

    log = await root_cause_agent.investigate_root_causes(
        investigation_id=inv_id,
        client_gstin=client_gstin,
        tax_period=tax_period,
        mismatch_amount=mismatch_amt,
        suspect_invoices=suspect_invoices
    )
    state["hypotheses"] = log.final_data.get("hypotheses", [])

    duration_ms = int((time.time() - t0) * 1000)
    hyp_count = len(state["hypotheses"])
    summary = f"Formulated {hyp_count} root-cause hypotheses via Tax Portal MCP inspection."

    await _save_agent_run(
        investigation_id=inv_id,
        agent_name="Root-Cause Investigator",
        status="COMPLETED",
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        duration_ms=duration_ms,
        task_desc=task_desc,
        output_summary=summary,
        steps=log.steps
    )

    await stream_manager.broadcast(inv_id, "agent_completed", {
        "agent_name": "Root-Cause Investigator",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "output_summary": summary,
        "hypotheses_count": hyp_count
    })

    return state

async def node_evidence_challenge(state: InvestigationWorkflowState) -> InvestigationWorkflowState:
    inv_id = state.get("investigation_id", "INV-UNKNOWN")
    logger.info("node_evidence_challenge", inv_id=inv_id)
    state["current_node"] = "EVIDENCE_CHALLENGE"
    state["step_history"].append("EVIDENCE_CHALLENGE")

    await stream_manager.broadcast(inv_id, "node_transition", {"node": "EVIDENCE_CHALLENGE"})

    started_at = datetime.now(timezone.utc)
    t0 = time.time()
    task_desc = "Executing ReAct Loop 3: Adversarially challenging evidence and classifying SUPPORTED/CONTRADICTED"
    await stream_manager.broadcast(inv_id, "agent_started", {
        "agent_name": "Evidence Challenge Engine",
        "status": "RUNNING",
        "task": task_desc,
        "started_at": started_at.isoformat()
    })

    notice = state.get("notice_data", {})
    client_gstin = notice.get("gstin") or state.get("client_gstin", "27AABCT1234C1Z5")
    tax_period = notice.get("tax_period", "2023-11")
    mismatch_amt = notice.get("itc_mismatch", 81000.0)
    proposed_hypotheses = state.get("hypotheses", [])

    log = await evidence_challenge_engine.challenge_hypotheses(
        investigation_id=inv_id,
        client_gstin=client_gstin,
        tax_period=tax_period,
        mismatch_amount=mismatch_amt,
        proposed_hypotheses=proposed_hypotheses,
        suspect_invoices=state.get("suspect_invoices", [])
    )
    state["evaluated_hypotheses"] = log.final_data.get("evaluated_hypotheses", [])

    duration_ms = int((time.time() - t0) * 1000)
    eval_count = len(state["evaluated_hypotheses"])
    summary = f"Challenged evidence independently: Classified {eval_count} findings (SUPPORTED, CONTRADICTED, UNVERIFIED)."

    await _save_agent_run(
        investigation_id=inv_id,
        agent_name="Evidence Challenge Engine",
        status="COMPLETED",
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        duration_ms=duration_ms,
        task_desc=task_desc,
        output_summary=summary,
        steps=log.steps
    )

    await stream_manager.broadcast(inv_id, "agent_completed", {
        "agent_name": "Evidence Challenge Engine",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "output_summary": summary,
        "evaluated_hypotheses": state["evaluated_hypotheses"]
    })

    return state

async def node_verification_gate(state: InvestigationWorkflowState) -> InvestigationWorkflowState:
    inv_id = state.get("investigation_id", "INV-UNKNOWN")
    logger.info("node_verification_gate", inv_id=inv_id)
    state["current_node"] = "VERIFICATION_GATE"
    state["step_history"].append("VERIFICATION_GATE")

    await stream_manager.broadcast(inv_id, "node_transition", {"node": "VERIFICATION_GATE"})
    
    started_at = datetime.now(timezone.utc)
    t0 = time.time()
    task_desc = "Executing deterministic statutory checks & ITC arithmetic reconciliation"
    await stream_manager.broadcast(inv_id, "agent_started", {
        "agent_name": "Verification Gate",
        "status": "RUNNING",
        "task": task_desc,
        "started_at": started_at.isoformat()
    })

    try:
        notice = state.get("notice_data", {})
        mismatch_amt = notice.get("itc_mismatch", 81000.0)
        suspect_invoices = state.get("suspect_invoices", [])
        evaluated_hypotheses = state.get("evaluated_hypotheses", [])

        gate_result = verification_gate.verify_investigation(
            notice_mismatch_amount=mismatch_amt,
            suspect_invoices=suspect_invoices,
            evaluated_hypotheses=evaluated_hypotheses,
            mismatch_results=state.get("mismatch_results"),
            fan_in_summary=state.get("fan_in_summary"),
            notice_tax_period=notice.get("tax_period"),
        )

        state["verification_passed"] = gate_result.is_approved
        state["verification_verdict"] = gate_result.verdict
        state["verification_details"] = gate_result.model_dump()

        duration_ms = int((time.time() - t0) * 1000)
        verified_cnt = len(gate_result.verified_findings)
        unresolved_cnt = len(gate_result.unresolved_matters)
        summary = f"Verification Gate verdict: {gate_result.verdict}. {verified_cnt} verified findings, {unresolved_cnt} unresolved matters."

        await _save_agent_run(
            investigation_id=inv_id,
            agent_name="Verification Gate",
            status="COMPLETED",
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            task_desc=task_desc,
            output_summary=summary
        )

        await stream_manager.broadcast(inv_id, "agent_completed", {
            "agent_name": "Verification Gate",
            "status": "COMPLETED",
            "duration_ms": duration_ms,
            "output_summary": summary,
            "is_approved": gate_result.is_approved,
            "verdict": gate_result.verdict,
            "verified_findings_count": verified_cnt,
            "unresolved_matters_count": unresolved_cnt
        })

        await stream_manager.broadcast(inv_id, "verification_gate_evaluated", {
            "is_approved": gate_result.is_approved,
            "verdict": gate_result.verdict,
            "checks": [c.model_dump() for c in gate_result.policy_results],
            "policy_results": [c.model_dump() for c in gate_result.policy_results],
            "verified_findings_count": verified_cnt,
            "unresolved_matters_count": unresolved_cnt
        })

    except Exception as exc:
        duration_ms = int((time.time() - t0) * 1000)
        err_msg = str(exc)
        logger.error("verification_gate_failed", error=err_msg, exc_info=True)
        await _save_agent_run(
            investigation_id=inv_id,
            agent_name="Verification Gate",
            status="FAILED",
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            task_desc=task_desc,
            error_message=err_msg
        )
        await stream_manager.broadcast(inv_id, "agent_failed", {
            "agent_name": "Verification Gate",
            "status": "FAILED",
            "error_message": err_msg,
            "duration_ms": duration_ms
        })
        state["error"] = err_msg

    return state

async def node_response_drafting(state: InvestigationWorkflowState) -> InvestigationWorkflowState:
    inv_id = state.get("investigation_id", "INV-UNKNOWN")
    logger.info("node_response_drafting", inv_id=inv_id)
    state["current_node"] = "RESPONSE_DRAFTING"
    state["step_history"].append("RESPONSE_DRAFTING")

    await stream_manager.broadcast(inv_id, "node_transition", {"node": "RESPONSE_DRAFTING"})

    started_at = datetime.now(timezone.utc)
    t0 = time.time()
    task_desc = "Drafting formal Section 16(2) compliance response restricted to verified evidence"
    await stream_manager.broadcast(inv_id, "agent_started", {
        "agent_name": "Response Drafter Agent",
        "status": "RUNNING",
        "task": task_desc,
        "started_at": started_at.isoformat()
    })

    try:
        client_name = state.get("client_name", "ABC Traders Pvt Ltd")
        client_gstin = state.get("client_gstin", "27AABCT1234C1Z5")
        notice_data = state.get("notice_data", {})
        v_details = state.get("verification_details", {})
        verified_findings = v_details.get("verified_findings", [])
        unresolved_matters = v_details.get("unresolved_matters", [])
        suspect_invoices = state.get("suspect_invoices", [])
        verification_passed = state.get("verification_passed", False)
        verification_verdict = state.get("verification_verdict", "INSUFFICIENT_EVIDENCE")

        draft = await response_drafter_agent.draft_response(
            investigation_id=inv_id,
            client_name=client_name,
            client_gstin=client_gstin,
            notice_data=notice_data,
            verified_findings=verified_findings,
            unresolved_matters=unresolved_matters,
            suspect_invoices=suspect_invoices,
            verification_passed=verification_passed,
            verification_verdict=verification_verdict
        )
        state["response_draft"] = draft.model_dump()
        state["approval_required"] = True
        state["approval_status"] = "NEEDS_MORE_EVIDENCE" if not verification_passed else "PENDING"

        duration_ms = int((time.time() - t0) * 1000)
        annexure_count = len(getattr(draft, "annexure_invoices", draft.verified_findings_schedule))
        summary = f"Prepared formal reply draft ({annexure_count} annexure invoices, Section 16(2) legal citations)."

        await _save_agent_run(
            investigation_id=inv_id,
            agent_name="Response Drafter Agent",
            status="COMPLETED",
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            task_desc=task_desc,
            output_summary=summary
        )

        await stream_manager.broadcast(inv_id, "agent_completed", {
            "agent_name": "Response Drafter Agent",
            "status": "COMPLETED",
            "duration_ms": duration_ms,
            "output_summary": summary,
            "response_draft": state["response_draft"]
        })

    except Exception as exc:
        duration_ms = int((time.time() - t0) * 1000)
        err_msg = str(exc)
        logger.error("response_drafting_failed", error=err_msg, exc_info=True)
        await _save_agent_run(
            investigation_id=inv_id,
            agent_name="Response Drafter Agent",
            status="FAILED",
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            task_desc=task_desc,
            error_message=err_msg
        )
        await stream_manager.broadcast(inv_id, "agent_failed", {
            "agent_name": "Response Drafter Agent",
            "status": "FAILED",
            "error_message": err_msg,
            "duration_ms": duration_ms
        })
        state["error"] = err_msg

    return state

async def node_accountant_approval(state: InvestigationWorkflowState) -> InvestigationWorkflowState:
    inv_id = state.get("investigation_id", "")
    logger.info("node_accountant_approval_awaiting_human", inv_id=inv_id)
    state["current_node"] = "ACCOUNTANT_APPROVAL"
    state["step_history"].append("ACCOUNTANT_APPROVAL")
    state["approval_required"] = True

    await stream_manager.broadcast(inv_id, "investigation_paused_for_approval", {
        "approval_required": True,
        "approval_status": "PENDING",
        "response_summary": state.get("response_draft", {}).get("factual_rebuttal", "Draft prepared and awaiting accountant approval")
    })
    return state

async def node_finalize_investigation(state: InvestigationWorkflowState) -> InvestigationWorkflowState:
    inv_id = state.get("investigation_id", "")
    logger.info("node_finalize_investigation", inv_id=inv_id)
    state["current_node"] = "FINALIZE_INVESTIGATION"
    state["step_history"].append("FINALIZE_INVESTIGATION")
    state["is_completed"] = True

    await stream_manager.broadcast(inv_id, "investigation_completed", {
        "is_completed": True
    })
    return state
