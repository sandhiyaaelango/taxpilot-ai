import uuid
import json
from typing import Dict, Any, Callable, Awaitable, Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, update
from app.workflows.state import InvestigationWorkflowState
from app.workflows.nodes import (
    node_load_investigation,
    node_parse_notice,
    node_validate_notice,
    node_build_investigation_plan,
    node_create_invoice_tasks,
    node_ledger_investigation,
    node_mismatch_fanout,
    node_fan_in,
    node_root_cause_investigation,
    node_evidence_challenge,
    node_verification_gate,
    node_response_drafting,
    node_accountant_approval,
    node_finalize_investigation
)
from app.database.session import AsyncSessionLocal
from app.database.models.agent import WorkflowCheckpoint
from app.database.models.investigation import Investigation
from app.config.logging import get_logger
from app.investigation.stream_manager import stream_manager

logger = get_logger("workflow_graph")

class TaxPilotWorkflowGraph:
    """
    TaxPilot AI Master Stateful Multi-Agent Investigation Workflow Graph.
    Implements persistent state, checkpointing, conditional routing, and human approval gates.
    """
    def __init__(self):
        self.nodes = {
            "LOAD_INVESTIGATION": node_load_investigation,
            "PARSE_NOTICE": node_parse_notice,
            "VALIDATE_NOTICE": node_validate_notice,
            "BUILD_INVESTIGATION_PLAN": node_build_investigation_plan,
            "CREATE_INVOICE_TASKS": node_create_invoice_tasks,
            "LEDGER_INVESTIGATION": node_ledger_investigation,
            "MISMATCH_FANOUT": node_mismatch_fanout,
            "FAN_IN": node_fan_in,
            "ROOT_CAUSE_INVESTIGATION": node_root_cause_investigation,
            "EVIDENCE_CHALLENGE": node_evidence_challenge,
            "VERIFICATION_GATE": node_verification_gate,
            "RESPONSE_DRAFTING": node_response_drafting,
            "ACCOUNTANT_APPROVAL": node_accountant_approval,
            "FINALIZE_INVESTIGATION": node_finalize_investigation
        }

    async def save_checkpoint(self, investigation_id: str, node_name: str, state: InvestigationWorkflowState) -> str:
        """Persist state checkpoint into database for reliable workflow recovery."""
        checkpoint_id = f"CHK-{node_name}-{uuid.uuid4().hex[:8]}"
        state["checkpoint_id"] = checkpoint_id
        try:
            async with AsyncSessionLocal() as session:
                # Mark previous checkpoints as not latest
                inv_uuid = uuid.UUID(investigation_id) if isinstance(investigation_id, str) and len(investigation_id) == 36 else None
                if inv_uuid:
                    await session.execute(
                        update(WorkflowCheckpoint)
                        .where(WorkflowCheckpoint.investigation_id == inv_uuid)
                        .values(is_latest=False)
                    )
                    checkpoint = WorkflowCheckpoint(
                        id=uuid.uuid4(),
                        investigation_id=inv_uuid,
                        checkpoint_id=checkpoint_id,
                        node_name=node_name,
                        state_data=state,
                        is_latest=True
                    )
                    session.add(checkpoint)

                    # Update investigation status
                    inv_status = "INVESTIGATING"
                    if node_name == "ACCOUNTANT_APPROVAL":
                        inv_status = "AWAITING_APPROVAL"
                    elif node_name == "FINALIZE_INVESTIGATION":
                        inv_status = "COMPLETED"
                    elif node_name == "VALIDATE_NOTICE" and not state.get("notice_valid"):
                        inv_status = "FAILED"

                    await session.execute(
                        update(Investigation)
                        .where(Investigation.id == inv_uuid)
                        .values(
                            status=inv_status,
                            workflow_state=state,
                            current_checkpoint_id=checkpoint_id
                        )
                    )
                    await session.commit()
        except Exception as e:
            logger.warning("failed_to_save_db_checkpoint", error=str(e))

        return checkpoint_id

    async def run(
        self,
        initial_state: InvestigationWorkflowState,
        start_from_node: str = "LOAD_INVESTIGATION"
    ) -> InvestigationWorkflowState:
        """
        Execute workflow step by step with checkpointing and conditional branching.
        Halts automatically at 'ACCOUNTANT_APPROVAL' for human review.
        """
        state = dict(initial_state)
        current = start_from_node
        inv_id = state.get("investigation_id", str(uuid.uuid4()))

        logger.info("workflow_execution_started", start_node=start_from_node, investigation_id=inv_id)

        while current:
            node_fn = self.nodes.get(current)
            if not node_fn:
                logger.error("unknown_workflow_node", node=current)
                state["error"] = f"Unknown node {current}"
                break

            # Execute Node
            state = await node_fn(state)
            await self.save_checkpoint(inv_id, current, state)

            # Determine Next Node via Conditional Routing
            current = self._route_next(current, state)

            # Human-in-the-Loop Approval Gate: Workflow pauses here!
            if current == "ACCOUNTANT_APPROVAL":
                state = await self.nodes["ACCOUNTANT_APPROVAL"](state)
                await self.save_checkpoint(inv_id, "ACCOUNTANT_APPROVAL", state)
                logger.info("workflow_paused_for_human_approval", investigation_id=inv_id)
                break

        logger.info("workflow_step_execution_concluded", current_node=state.get("current_node"))
        return state

    def _route_next(self, current_node: str, state: InvestigationWorkflowState) -> Optional[str]:
        """Conditional routing logic."""
        if current_node == "LOAD_INVESTIGATION":
            return "PARSE_NOTICE"
        
        elif current_node == "PARSE_NOTICE":
            return "VALIDATE_NOTICE"
        
        elif current_node == "VALIDATE_NOTICE":
            # Conditional Edge 1: Notice Validation
            if not state.get("notice_valid", False):
                logger.warning("notice_validation_failed_stopping")
                return None
            return "BUILD_INVESTIGATION_PLAN"

        elif current_node == "BUILD_INVESTIGATION_PLAN":
            return "CREATE_INVOICE_TASKS"

        elif current_node == "CREATE_INVOICE_TASKS":
            return "LEDGER_INVESTIGATION"

        elif current_node == "LEDGER_INVESTIGATION":
            return "MISMATCH_FANOUT"

        elif current_node == "MISMATCH_FANOUT":
            return "FAN_IN"

        elif current_node == "FAN_IN":
            return "ROOT_CAUSE_INVESTIGATION"

        elif current_node == "ROOT_CAUSE_INVESTIGATION":
            return "EVIDENCE_CHALLENGE"

        elif current_node == "EVIDENCE_CHALLENGE":
            return "VERIFICATION_GATE"

        elif current_node == "VERIFICATION_GATE":
            # Conditional Edge 2: Verification Gate Verdict
            # Always proceed to RESPONSE_DRAFTING; if evidence is insufficient, Response Drafter
            # marks the draft as NEEDS_AUDITOR_INPUT with missing-document disclosures.
            if not state.get("verification_passed", False):
                logger.warning("verification_gate_insufficient_evidence_drafting_needs_input")
                state["approval_status"] = "NEEDS_MORE_EVIDENCE"
            return "RESPONSE_DRAFTING"

        elif current_node == "RESPONSE_DRAFTING":
            return "ACCOUNTANT_APPROVAL"

        elif current_node == "ACCOUNTANT_APPROVAL":
            # Conditional Edge 3: Human Reviewer Action
            status = state.get("approval_status")
            if status == "APPROVED":
                return "FINALIZE_INVESTIGATION"
            return None  # Remains paused

        elif current_node == "FINALIZE_INVESTIGATION":
            return None

        return None

workflow_graph = TaxPilotWorkflowGraph()
