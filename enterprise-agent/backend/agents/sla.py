"""
agents/sla.py — SLA Breach Prevention Agent (Module 4)

Scenario: A procurement approval stuck for 48+ hours.
Steps:
  1. Scan pending approvals for SLA breaches
  2. Identify the bottleneck (approver on leave)
  3. Find the delegate
  4. Reroute approval to delegate
  5. Log the override with full audit trail
  6. Notify all parties

Demonstrates: autonomous bottleneck detection, delegate rerouting, compliance audit.
"""
import os
from models.state import AgentState
from tools import (
    approvals_get_pending, approvals_reroute, approvals_log_override,
    hr_get_employee_info,
    slack_send_message, email_send,
)
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

SLA_THRESHOLD_HOURS = 24


def _get_llm() -> ChatGroq:
    return ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"), temperature=0)


BOTTLENECK_SYSTEM = """You are an enterprise workflow analyst.
Given an approval record and approver info, write a 1-sentence plain-English explanation
of why the approval is stuck. Be specific. No preamble.
"""


async def run_sla_agent(state: AgentState) -> AgentState:
    state.status = "running"

    # ── Step 1: Scan for SLA breaches ──────────────────────────────────────
    state.current_step = "scan_approvals"
    state.log("scan_approvals", "running", f"Scanning pending approvals (SLA threshold: {SLA_THRESHOLD_HOURS}h)")

    pending = await approvals_get_pending(threshold_hours=SLA_THRESHOLD_HOURS)
    breached = [a for a in pending if a["hours_pending"] >= SLA_THRESHOLD_HOURS]

    state.log(
        "scan_approvals", "success",
        f"Found {len(pending)} pending, {len(breached)} SLA-breached",
        "approvals_db", str(pending),
    )
    state.mark_step_done("scan_approvals")
    state.output["breached_approvals"] = breached

    if not breached:
        state.log("scan_approvals", "success", "No SLA breaches. All approvals on track.")
        state.status = "success"
        return state

    # Process the first breached approval (extend for multiple)
    approval = breached[0]
    approval_id  = approval["approval_id"]
    approver_id  = approval["approver_id"]

    # ── Step 2: Identify bottleneck ────────────────────────────────────────
    state.current_step = "identify_bottleneck"
    state.log("identify_bottleneck", "running", f"Fetching info for approver {approver_id}")

    approver_info = await hr_get_employee_info(approver_id)
    state.log("identify_bottleneck", "success", f"Approver info fetched: on_leave={approver_info.get('on_leave')}", "hr_system", str(approver_info))

    # Use small LLM to explain the bottleneck in plain English
    llm = _get_llm()
    explanation = await llm.ainvoke([
        SystemMessage(content=BOTTLENECK_SYSTEM),
        HumanMessage(content=f"Approval: {approval}\nApprover info: {approver_info}"),
    ])
    bottleneck_reason = explanation.content.strip()

    state.log("identify_bottleneck", "success", f"Bottleneck: {bottleneck_reason}", "groq_llm")
    state.mark_step_done("identify_bottleneck")
    state.output["bottleneck_reason"] = bottleneck_reason
    state.output["approver_info"] = approver_info

    # ── Step 3: Find delegate ──────────────────────────────────────────────
    state.current_step = "find_delegate"
    delegate_id = approver_info.get("delegate") or approver_info.get("manager")

    if not delegate_id:
        state.log("find_delegate", "escalated", "No delegate or manager found — escalating to HR")
        state.escalation_required = True
        state.escalation_target = "HR Team"
        state.status = "escalated"
        return state

    delegate_info = await hr_get_employee_info(delegate_id)
    state.log(
        "find_delegate", "success",
        f"Delegate found: {delegate_info.get('name')} ({delegate_id})",
        "hr_system", str(delegate_info),
    )
    state.mark_step_done("find_delegate")
    state.output["delegate"] = {**delegate_info, "id": delegate_id}

    # ── Step 4: Reroute approval ───────────────────────────────────────────
    state.current_step = "reroute_approval"
    reroute_reason = (
        f"Original approver {approver_info.get('name')} ({approver_id}) is on leave. "
        f"Approval {approval_id} has been pending {approval['hours_pending']}h, breaching {SLA_THRESHOLD_HOURS}h SLA. "
        f"Auto-rerouted to delegate per SLA policy."
    )
    reroute_result = await approvals_reroute(
        approval_id=approval_id,
        from_id=approver_id,
        to_id=delegate_id,
        reason=reroute_reason,
    )
    state.log(
        "reroute_approval", "success",
        f"Rerouted {approval_id} from {approver_id} → {delegate_id}",
        "approvals_db", str(reroute_result),
    )
    state.mark_step_done("reroute_approval")
    state.output["reroute_result"] = reroute_result

    # ── Step 5: Log compliance override ───────────────────────────────────
    state.current_step = "log_override"
    audit_result = await approvals_log_override(
        approval_id=approval_id,
        override_by="SLA-Breach-Agent-v1",
        reason=reroute_reason,
    )
    state.log(
        "log_override", "success",
        f"Override logged. Compliance ref: {audit_result['compliance_ref']}",
        "compliance_db", str(audit_result),
    )
    state.mark_step_done("log_override")
    state.output["audit_result"] = audit_result

    # ── Step 6: Notify all parties ─────────────────────────────────────────
    state.current_step = "notify_parties"
    delegate_name = delegate_info.get("name", delegate_id)
    approver_name = approver_info.get("name", approver_id)

    # Notify delegate via Slack
    await slack_send_message(
        channel=f"@{delegate_id.lower()}",
        message=(
            f"🔔 *Action required:* Approval *{approval_id}* has been rerouted to you.\n"
            f"*Reason:* {approver_name} is on leave. Pending {approval['hours_pending']}h.\n"
            f"*Amount:* ₹{approval['amount']:,}\n"
            f"*Compliance ref:* {audit_result['compliance_ref']}"
        ),
    )

    # Notify requestor via email
    await email_send(
        to=["procurement@company.com"],
        subject=f"Approval {approval_id} rerouted — SLA action taken",
        body=(
            f"Approval {approval_id} was stuck for {approval['hours_pending']} hours.\n\n"
            f"Bottleneck: {bottleneck_reason}\n\n"
            f"Action taken: Rerouted to {delegate_name} ({delegate_id}).\n"
            f"Audit reference: {audit_result['compliance_ref']}\n\n"
            f"— SLA Breach Prevention Agent"
        ),
    )

    state.log("notify_parties", "success", f"Slack + email notifications sent to {delegate_name} and procurement team")
    state.mark_step_done("notify_parties")

    state.status = "success"
    return state
