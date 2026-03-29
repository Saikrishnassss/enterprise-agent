"""
agents/onboarding.py — Employee Onboarding Agent (Module 2)

Scenario: New hire joins Monday.
Steps:
  1. Create HR record
  2. Create Slack account
  3. Create JIRA account  ← intentional failure → retry → IT escalation
  4. Create Calendar account
  5. Assign buddy
  6. Schedule orientation meetings
  7. Send welcome pack

Demonstrates: 7 sequential steps, error recovery, escalation, full audit trail.
"""
import asyncio
from models.state import AgentState
from tools import (
    hr_create_employee_record, hr_assign_buddy,
    jira_create_account,
    slack_create_channel, slack_send_message,
    calendar_schedule_meeting,
    email_send, it_raise_ticket,
)

MAX_RETRIES = 3


async def run_onboarding_agent(state: AgentState) -> AgentState:
    """Entry point. Runs all 7 steps sequentially with error recovery."""
    payload = state.input_payload
    emp_id   = payload.get("employee_id", "EMP-NEW-001")
    name     = payload.get("name", "New Employee")
    dept     = payload.get("department", "Engineering")
    manager  = payload.get("manager_id", "EMP005")
    buddy    = payload.get("buddy_id", "EMP003")

    state.status = "running"

    # ── Step 1: HR record ──────────────────────────────────────────────────
    state.current_step = "create_hr_record"
    state.log("create_hr_record", "running", f"Creating HR record for {name}")
    try:
        result = await hr_create_employee_record(emp_id, name, dept)
        state.log("create_hr_record", "success", f"HR record created: {result['record_id']}", "hr_system", str(result))
        state.mark_step_done("create_hr_record")
        state.output["hr_record"] = result
    except Exception as e:
        state.log("create_hr_record", "failed", str(e))
        state.status = "failed"
        return state

    # ── Step 2: Slack account ──────────────────────────────────────────────
    state.current_step = "create_slack_account"
    state.log("create_slack_account", "running", f"Setting up Slack for {name}")
    try:
        channel = await slack_create_channel(f"onboarding-{emp_id.lower()}", [emp_id, manager])
        state.log("create_slack_account", "success", f"Slack channel created: {channel['name']}", "slack", str(channel))
        state.mark_step_done("create_slack_account")
        state.output["slack"] = channel
    except Exception as e:
        state.log("create_slack_account", "failed", str(e))
        # Non-critical — continue
        state.output["slack"] = {"error": str(e)}

    # ── Step 3: JIRA account (with retry + escalation) ─────────────────────
    state.current_step = "create_jira_account"
    jira_success = False
    for attempt in range(1, MAX_RETRIES + 1):
        state.retry_count = attempt - 1
        state.log(
            "create_jira_account", "running",
            f"Attempt {attempt}/{MAX_RETRIES}: Creating JIRA account for {name} (role=developer)",
            "jira",
        )
        try:
            result = await jira_create_account(emp_id, "developer")
            state.log("create_jira_account", "success", f"JIRA account created: {result['jira_user']}", "jira", str(result))
            state.mark_step_done("create_jira_account")
            state.output["jira"] = result
            jira_success = True
            break
        except ConnectionError as e:
            state.log("create_jira_account", "failed", f"Attempt {attempt} failed: {e}", "jira")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.5)  # back-off

    if not jira_success:
        # Escalate to IT
        state.escalation_required = True
        state.escalation_target = "IT Support"
        ticket = await it_raise_ticket(
            subject=f"JIRA access setup failed for {name} ({emp_id})",
            description=f"Auto-onboarding failed to provision JIRA after {MAX_RETRIES} attempts. Manual provisioning required.",
            priority="high",
        )
        state.log(
            "create_jira_account", "escalated",
            f"Escalated to IT after {MAX_RETRIES} failed attempts. Ticket: {ticket['ticket_id']}",
            "it_helpdesk", str(ticket),
            escalated_to="IT Support",
        )
        state.output["jira_escalation"] = ticket

    # ── Step 4: Calendar account ───────────────────────────────────────────
    state.current_step = "create_calendar_account"
    state.log("create_calendar_account", "running", f"Provisioning Google Calendar for {name}")
    try:
        # Calendar provisioning is simulated as always succeeding
        state.log("create_calendar_account", "success", f"Calendar provisioned for {emp_id}", "google_workspace")
        state.mark_step_done("create_calendar_account")
        state.output["calendar"] = {"provisioned": True, "email": f"{emp_id.lower()}@company.com"}
    except Exception as e:
        state.log("create_calendar_account", "failed", str(e))

    # ── Step 5: Assign buddy ───────────────────────────────────────────────
    state.current_step = "assign_buddy"
    state.log("assign_buddy", "running", f"Assigning buddy {buddy} to {emp_id}")
    try:
        result = await hr_assign_buddy(emp_id, buddy)
        state.log("assign_buddy", "success", f"Buddy {buddy} assigned and notified", "hr_system", str(result))
        state.mark_step_done("assign_buddy")
        state.output["buddy"] = result
    except Exception as e:
        state.log("assign_buddy", "failed", str(e))

    # ── Step 6: Schedule orientation ──────────────────────────────────────
    state.current_step = "schedule_orientation"
    state.log("schedule_orientation", "running", "Scheduling orientation meetings")
    try:
        orientation = await calendar_schedule_meeting(
            title=f"Welcome & Orientation — {name}",
            attendees=[emp_id, manager, buddy, "hr-team@company.com"],
            duration_mins=90,
            notes="New hire orientation. Please join on time.",
        )
        manager_sync = await calendar_schedule_meeting(
            title=f"Manager 1:1 — {name}",
            attendees=[emp_id, manager],
            duration_mins=30,
        )
        state.log("schedule_orientation", "success",
                  f"Orientation event: {orientation['event_id']}, Manager 1:1: {manager_sync['event_id']}",
                  "google_calendar", str(orientation))
        state.mark_step_done("schedule_orientation")
        state.output["meetings"] = [orientation, manager_sync]
    except Exception as e:
        state.log("schedule_orientation", "failed", str(e))

    # ── Step 7: Welcome pack email ─────────────────────────────────────────
    state.current_step = "send_welcome_pack"
    state.log("send_welcome_pack", "running", f"Sending welcome pack to {name}")

    meet_link = state.output.get("meetings", [{}])[0].get("meet_link", "TBD")
    jira_note = (
        f"JIRA: Your account is being set up manually (Ticket {state.output.get('jira_escalation', {}).get('ticket_id', 'N/A')}). "
        "You'll receive credentials within 2 hours."
        if not jira_success else
        f"JIRA: {state.output.get('jira', {}).get('jira_user', '')}"
    )
    body = f"""
Hi {name},

Welcome to the team! 🎉

Here's everything you need to get started:

• HR Record: {state.output.get('hr_record', {}).get('record_id', 'N/A')}
• Slack: #{state.output.get('slack', {}).get('name', 'N/A')}
• {jira_note}
• Orientation meeting: {meet_link}
• Your buddy: {buddy} — they'll reach out on Slack today

See you Monday!

— People & Culture Team (Automated Onboarding Agent)
""".strip()

    try:
        result = await email_send(
            to=[f"{emp_id.lower()}@personal.com"],
            subject=f"Welcome to the team, {name.split()[0]}! 🎉",
            body=body,
        )
        state.log("send_welcome_pack", "success", f"Welcome email sent. Message ID: {result['message_id']}", "email", str(result))
        state.mark_step_done("send_welcome_pack")
        state.output["welcome_email"] = result
    except Exception as e:
        state.log("send_welcome_pack", "failed", str(e))

    # ── Final status ───────────────────────────────────────────────────────
    if state.escalation_required:
        state.status = "escalated"
    else:
        state.status = "success"

    return state
