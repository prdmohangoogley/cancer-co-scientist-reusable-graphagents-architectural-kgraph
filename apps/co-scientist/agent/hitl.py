"""Human-in-the-Loop (HITL) Gatekeeper for High-Stakes Clinical Actions.

Conforms to:
- DOC-02: Zero Ambient Authority (ZAA) & Agentic SecOps (Mandatory Human Sign-off)
- DOC-03: Open AI Agent Protocol Stack & A2UI Declarative Interfaces
- Spec 15 §3: Enterprise Hardening and HITL Gatekeeper

Prevents autonomous execution of irreversible or hazardous medical actions, such as:
1. OFF_LABEL_THERAPY_RECOMMENDATION
2. EXPERIMENTAL_CLINICAL_TRIAL_ENROLLMENT
3. HIGH_TOXICITY_REGIMEN_MODIFICATION
4. EXPENSIVE_CLUSTER_SIMULATION
5. PATIENT_RECORD_STATE_MUTATION
"""

from __future__ import annotations

import enum
import secrets
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

try:
    from graphagent.observability.telemetry import emit_cloud_log
except (ImportError, ModuleNotFoundError):
    try:
        from observability.telemetry import emit_cloud_log
    except (ImportError, ModuleNotFoundError):
        try:
            from packages.graphagent.observability.telemetry import emit_cloud_log
        except (ImportError, ModuleNotFoundError):
            def emit_cloud_log(*args: Any, **kwargs: Any) -> None:
                pass


class ActionType(str, enum.Enum):
    """Categorization of high-stakes clinical and computational actions."""
    OFF_LABEL_THERAPY_RECOMMENDATION = "OFF_LABEL_THERAPY_RECOMMENDATION"
    EXPERIMENTAL_CLINICAL_TRIAL_ENROLLMENT = "EXPERIMENTAL_CLINICAL_TRIAL_ENROLLMENT"
    HIGH_TOXICITY_REGIMEN_MODIFICATION = "HIGH_TOXICITY_REGIMEN_MODIFICATION"
    EXPENSIVE_CLUSTER_SIMULATION = "EXPENSIVE_CLUSTER_SIMULATION"
    PATIENT_RECORD_STATE_MUTATION = "PATIENT_RECORD_STATE_MUTATION"
    OTHER_HIGH_RISK_ACTION = "OTHER_HIGH_RISK_ACTION"


class RiskLevel(str, enum.Enum):
    """Risk tier assessed for the proposed action."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApprovalStatus(str, enum.Enum):
    """State machine status for pending action requests."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ClinicalAction(BaseModel):
    """Represents a high-stakes clinical or computational action requiring sign-off."""
    action_id: str
    session_id: str = "default-session"
    action_type: str
    proposed_action: str
    clinical_rationale: str
    risk_level: str = RiskLevel.HIGH.value
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=30))
    reviewer_id: Optional[str] = None
    reviewer_comments: Optional[str] = None
    resolved_at: Optional[datetime] = None
    confirmation_token: str = Field(default_factory=lambda: secrets.token_urlsafe(16))

    def is_expired(self) -> bool:
        """Returns True if the action has expired past its expiration horizon."""
        if self.status != ApprovalStatus.PENDING:
            return False
        return datetime.now(timezone.utc) > self.expires_at


class ClinicalActionApprovalManager:
    """Thread-safe registry managing high-stakes action approvals and human confirmations."""

    def __init__(self) -> None:
        self._actions: Dict[str, ClinicalAction] = {}
        self._lock = threading.Lock()

    def create_action(
        self,
        action_type: str,
        proposed_action: str,
        clinical_rationale: str,
        risk_level: str = RiskLevel.HIGH.value,
        parameters: Optional[Dict[str, Any]] = None,
        session_id: str = "default-session",
        expires_in_minutes: int = 30,
    ) -> ClinicalAction:
        """Registers a pending clinical action and generates an approval ticket.

        Args:
            action_type: Categorical classification (e.g. OFF_LABEL_THERAPY_RECOMMENDATION).
            proposed_action: Concise description of the proposed clinical/computational action.
            clinical_rationale: Justification with genomic/biomedical evidence citations.
            risk_level: Assessed risk tier ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL').
            parameters: Payload details and parameter arguments.
            session_id: Associated conversation session identifier.
            expires_in_minutes: Expiration window before action auto-expires.

        Returns:
            ClinicalAction instance in PENDING status.
        """
        action_id = f"act-{secrets.token_hex(6)}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=expires_in_minutes)

        action = ClinicalAction(
            action_id=action_id,
            session_id=session_id,
            action_type=action_type,
            proposed_action=proposed_action,
            clinical_rationale=clinical_rationale,
            risk_level=risk_level,
            parameters=parameters or {},
            status=ApprovalStatus.PENDING,
            created_at=now,
            expires_at=expires_at,
        )

        with self._lock:
            self._actions[action_id] = action

        emit_cloud_log(
            "INFO",
            f"[HITL] Registered high-stakes action {action_id} of type '{action_type}' (Risk: {risk_level})",
            action_id=action_id,
            action_type=action_type,
            risk_level=risk_level,
        )
        return action

    def get_action(self, action_id: str) -> Optional[ClinicalAction]:
        """Retrieves an action by its unique ID, updating status if expired."""
        with self._lock:
            action = self._actions.get(action_id)
            if action and action.is_expired():
                action.status = ApprovalStatus.EXPIRED
            return action

    def list_pending(self, session_id: Optional[str] = None) -> List[ClinicalAction]:
        """Lists all active pending actions, filtering out expired tickets."""
        with self._lock:
            pending = []
            for action in self._actions.values():
                if action.is_expired():
                    action.status = ApprovalStatus.EXPIRED
                elif action.status == ApprovalStatus.PENDING:
                    if session_id is None or action.session_id == session_id:
                        pending.append(action)
            return pending

    def approve_action(
        self,
        action_id: str,
        reviewer_id: str = "clinician@cancercenter.org",
        comments: Optional[str] = None,
    ) -> ClinicalAction:
        """Approves a pending action, recording audit metadata."""
        with self._lock:
            action = self._actions.get(action_id)
            if not action:
                raise KeyError(f"Action '{action_id}' not found.")
            if action.is_expired():
                action.status = ApprovalStatus.EXPIRED
                raise ValueError(f"Action '{action_id}' has expired and cannot be approved.")
            if action.status != ApprovalStatus.PENDING:
                raise ValueError(f"Action '{action_id}' is already {action.status.value}.")

            action.status = ApprovalStatus.APPROVED
            action.reviewer_id = reviewer_id
            action.reviewer_comments = comments
            action.resolved_at = datetime.now(timezone.utc)

        emit_cloud_log(
            "INFO",
            f"[HITL] Action {action_id} APPROVED by {reviewer_id}",
            action_id=action_id,
            reviewer_id=reviewer_id,
        )
        return action

    def reject_action(
        self,
        action_id: str,
        reviewer_id: str = "clinician@cancercenter.org",
        comments: Optional[str] = None,
    ) -> ClinicalAction:
        """Rejects a pending action, recording audit metadata."""
        with self._lock:
            action = self._actions.get(action_id)
            if not action:
                raise KeyError(f"Action '{action_id}' not found.")
            if action.is_expired():
                action.status = ApprovalStatus.EXPIRED
                raise ValueError(f"Action '{action_id}' has expired and cannot be rejected.")
            if action.status != ApprovalStatus.PENDING:
                raise ValueError(f"Action '{action_id}' is already {action.status.value}.")

            action.status = ApprovalStatus.REJECTED
            action.reviewer_id = reviewer_id
            action.reviewer_comments = comments
            action.resolved_at = datetime.now(timezone.utc)

        emit_cloud_log(
            "WARNING",
            f"[HITL] Action {action_id} REJECTED by {reviewer_id}",
            action_id=action_id,
            reviewer_id=reviewer_id,
        )
        return action

    def to_a2ui_card(self, action: ClinicalAction) -> Dict[str, Any]:
        """Renders the action as a declarative A2UI ConfirmationDialog / HumanApprovalCard schema.

        Conforms strictly to DOC-03 (Declarative Non-executable JSON).
        """
        return {
            "type": "ConfirmationDialog",
            "component_id": f"hitl-{action.action_id}",
            "title": f"Clinician Confirmation Required: {action.action_type.replace('_', ' ').title()}",
            "severity": "critical" if action.risk_level in ("HIGH", "CRITICAL") else "warning",
            "action_id": action.action_id,
            "risk_level": action.risk_level,
            "proposed_action": action.proposed_action,
            "clinical_rationale": action.clinical_rationale,
            "parameters": action.parameters,
            "status": action.status.value,
            "expires_at": action.expires_at.isoformat(),
            "actions": [
                {
                    "label": "Approve Clinical Action",
                    "action": "APPROVE",
                    "style": "primary-danger" if action.risk_level == "CRITICAL" else "primary",
                    "endpoint": f"/api/actions/{action.action_id}/approve",
                    "method": "POST",
                },
                {
                    "label": "Reject & Provide Feedback",
                    "action": "REJECT",
                    "style": "secondary",
                    "endpoint": f"/api/actions/{action.action_id}/reject",
                    "method": "POST",
                },
            ],
        }


# Global singleton instance
clinical_approval_manager = ClinicalActionApprovalManager()
