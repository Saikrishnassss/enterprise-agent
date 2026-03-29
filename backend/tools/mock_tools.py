"""
tools/mock_tools.py — Simulated enterprise integrations.

Every tool can be configured to succeed, fail, or be slow.
Inject TOOL_FAILURE_MAP in tests to simulate real error scenarios.
"""
import asyncio
import random
from typing import Any, Optional

# ── Failure injection map ──────────────────────────────────────────────────
# Set a tool name to True to force it to fail (used in demo / tests)
TOOL_FAILURE_MAP: dict[str, bool] = {
    "jira_create_account": True,   # Simulates JIRA access error for onboarding demo
}


async def _simulate_latency(min_ms: int = 200, max_ms: int = 800) -> None:
    await asyncio.sleep(random.uniform(min_ms, max_ms) / 1000)


# ── JIRA ───────────────────────────────────────────────────────────────────

async def jira_create_account(employee_id: str, role: str) -> dict[str, Any]:
    await _simulate_latency()
    if TOOL_FAILURE_MAP.get("jira_create_account"):
        raise ConnectionError(f"JIRA API error 403: insufficient permissions for role={role}")
    return {"status": "created", "jira_user": f"{employee_id}@company.com", "role": role}


async def jira_create_task(title: str, assignee: str, project: str) -> dict[str, Any]:
    await _simulate_latency()
    task_id = f"{project}-{random.randint(1000, 9999)}"
    return {"task_id": task_id, "url": f"https://jira.company.com/browse/{task_id}", "assignee": assignee}


# ── HR System ──────────────────────────────────────────────────────────────

async def hr_create_employee_record(employee_id: str, name: str, department: str) -> dict[str, Any]:
    await _simulate_latency()
    return {"employee_id": employee_id, "record_id": f"HR-{employee_id}", "status": "active"}


async def hr_get_employee_info(employee_id: str) -> dict[str, Any]:
    await _simulate_latency()
    mock_employees = {
        "EMP001": {"name": "Priya Sharma", "department": "Engineering", "on_leave": False, "manager": "EMP005"},
        "EMP002": {"name": "Arjun Mehta", "department": "Product", "on_leave": True, "delegate": "EMP003"},
        "EMP003": {"name": "Kavya Reddy", "department": "Product", "on_leave": False, "manager": "EMP005"},
        "EMP005": {"name": "Rahul Verma", "department": "Engineering", "on_leave": False, "manager": "EMP010"},
    }
    return mock_employees.get(employee_id, {"error": "Employee not found"})


async def hr_assign_buddy(new_hire_id: str, buddy_id: str) -> dict[str, Any]:
    await _simulate_latency()
    return {"status": "assigned", "new_hire": new_hire_id, "buddy": buddy_id, "notification_sent": True}


# ── Google Calendar ────────────────────────────────────────────────────────

async def calendar_schedule_meeting(
    title: str, attendees: list[str], duration_mins: int, notes: str = ""
) -> dict[str, Any]:
    await _simulate_latency()
    return {
        "event_id": f"CAL-{random.randint(10000, 99999)}",
        "title": title,
        "attendees": attendees,
        "scheduled_at": "2026-04-07T10:00:00Z",
        "meet_link": "https://meet.google.com/abc-defg-hij",
    }


# ── Slack ──────────────────────────────────────────────────────────────────

async def slack_send_message(channel: str, message: str, blocks: Optional[list] = None) -> dict[str, Any]:
    await _simulate_latency(50, 200)
    return {"ok": True, "channel": channel, "ts": f"{random.uniform(1700000000, 1800000000):.6f}"}


async def slack_create_channel(name: str, members: list[str]) -> dict[str, Any]:
    await _simulate_latency()
    return {"channel_id": f"C{random.randint(10000000, 99999999)}", "name": name, "members": members}


# ── Email ──────────────────────────────────────────────────────────────────

async def email_send(to: list[str], subject: str, body: str, html: bool = False) -> dict[str, Any]:
    await _simulate_latency(100, 400)
    return {"sent": True, "recipients": to, "subject": subject, "message_id": f"MSG-{random.randint(10000, 99999)}"}


# ── Approvals / Procurement DB ─────────────────────────────────────────────

async def approvals_get_pending(threshold_hours: int = 24) -> list[dict[str, Any]]:
    await _simulate_latency()
    return [
        {
            "approval_id": "APR-2891",
            "title": "Vendor contract — Infra upgrade Q2",
            "amount": 142000,
            "approver_id": "EMP002",
            "submitted_at": "2026-03-27T08:00:00Z",
            "hours_pending": 49,
            "status": "pending",
        }
    ]


async def approvals_reroute(approval_id: str, from_id: str, to_id: str, reason: str) -> dict[str, Any]:
    await _simulate_latency()
    return {
        "approval_id": approval_id,
        "rerouted_from": from_id,
        "rerouted_to": to_id,
        "reason": reason,
        "audit_ref": f"AUDIT-{random.randint(1000, 9999)}",
        "timestamp": "2026-03-29T12:00:00Z",
    }


async def approvals_log_override(approval_id: str, override_by: str, reason: str) -> dict[str, Any]:
    await _simulate_latency(50, 150)
    return {
        "logged": True,
        "approval_id": approval_id,
        "override_by": override_by,
        "reason": reason,
        "compliance_ref": f"COMP-{random.randint(10000, 99999)}",
    }


# ── IT Escalation ──────────────────────────────────────────────────────────

async def it_raise_ticket(subject: str, description: str, priority: str = "high") -> dict[str, Any]:
    await _simulate_latency()
    return {
        "ticket_id": f"IT-{random.randint(1000, 9999)}",
        "subject": subject,
        "priority": priority,
        "assigned_to": "it-support@company.com",
        "eta_hours": 2,
    }
