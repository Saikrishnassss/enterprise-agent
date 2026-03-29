from .mock_tools import (
    jira_create_account, jira_create_task,
    hr_create_employee_record, hr_get_employee_info, hr_assign_buddy,
    calendar_schedule_meeting,
    slack_send_message, slack_create_channel,
    email_send,
    approvals_get_pending, approvals_reroute, approvals_log_override,
    it_raise_ticket,
    TOOL_FAILURE_MAP,
)
