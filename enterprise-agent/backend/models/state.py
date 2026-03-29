"""
models/state.py — Shared state models for all agents.
Every agent reads from and writes to AgentState as it flows through the graph.
"""
from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


ScenarioType = Literal["onboarding", "meeting", "sla"]
StepStatus  = Literal["pending", "running", "success", "failed", "escalated", "waiting_human"]


class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    scenario: ScenarioType
    step: str
    status: StepStatus
    detail: str
    tool_called: Optional[str] = None
    tool_result: Optional[str] = None
    retry_count: int = 0
    escalated_to: Optional[str] = None


class AgentState(BaseModel):
    """Unified state object that flows through the LangGraph state machine."""
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario: ScenarioType
    input_payload: dict[str, Any] = {}
    steps_completed: list[str] = []
    audit_log: list[AuditEntry] = []
    current_step: str = ""
    status: StepStatus = "pending"
    retry_count: int = 0
    error_message: Optional[str] = None
    escalation_required: bool = False
    escalation_target: Optional[str] = None
    human_clarification_needed: Optional[str] = None
    output: dict[str, Any] = {}

    def log(
        self,
        step: str,
        status: StepStatus,
        detail: str,
        tool_called: Optional[str] = None,
        tool_result: Optional[str] = None,
        escalated_to: Optional[str] = None,
    ) -> None:
        entry = AuditEntry(
            scenario=self.scenario,
            step=step,
            status=status,
            detail=detail,
            tool_called=tool_called,
            tool_result=tool_result,
            retry_count=self.retry_count,
            escalated_to=escalated_to,
        )
        self.audit_log.append(entry)

    def mark_step_done(self, step: str) -> None:
        if step not in self.steps_completed:
            self.steps_completed.append(step)
        self.current_step = step
