"""
agents/meeting.py — Meeting-to-Action Agent (Module 3)

Scenario: Given a meeting transcript (4 participants), the agent must:
  1. Parse transcript with LLM
  2. Extract action items
  3. Assign owners based on context
  4. Flag ambiguous items (no clear owner) — asks for clarification
  5. Create tasks in JIRA
  6. Send summary email to all participants

Demonstrates: LLM reasoning, ambiguity handling, clarification flow.
"""
import json
import os
from models.state import AgentState
from tools import jira_create_task, email_send, slack_send_message
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


def _get_llm(large: bool = True) -> ChatGroq:
    """Smart routing: large model for reasoning, small for classification."""
    model = "llama-3.3-70b-versatile" if large else "llama-3.1-8b-instant"
    return ChatGroq(model=model, api_key=os.getenv("GROQ_API_KEY"), temperature=0.1)


EXTRACTION_SYSTEM = """You are an enterprise meeting analyst.
Given a meeting transcript, extract ALL action items.
For each item return JSON with:
  - title: short task title
  - description: what needs to be done
  - owner: person's name if clearly mentioned, else null
  - due_hint: any due date mentioned, else null
  - ambiguous: true if ownership is unclear

Return ONLY a JSON array. No preamble or markdown.
"""


async def run_meeting_agent(state: AgentState) -> AgentState:
    payload    = state.input_payload
    transcript = payload.get("transcript", "")
    participants = payload.get("participants", [])
    project    = payload.get("jira_project", "PROJ")

    state.status = "running"

    # ── Step 1: Parse transcript ───────────────────────────────────────────
    state.current_step = "parse_transcript"
    state.log("parse_transcript", "running", f"Parsing transcript ({len(transcript)} chars, {len(participants)} participants)")

    llm = _get_llm(large=True)
    messages = [
        SystemMessage(content=EXTRACTION_SYSTEM),
        HumanMessage(content=f"Participants: {', '.join(participants)}\n\nTranscript:\n{transcript}"),
    ]
    response = await llm.ainvoke(messages)
    raw = response.content.strip()

    state.log("parse_transcript", "success", "LLM extraction complete", "groq_llm", raw[:200])
    state.mark_step_done("parse_transcript")

    # ── Step 2: Parse action items ─────────────────────────────────────────
    state.current_step = "extract_action_items"
    try:
        # Strip markdown fences if model added them
        clean = raw.replace("```json", "").replace("```", "").strip()
        action_items: list[dict] = json.loads(clean)
    except json.JSONDecodeError as e:
        state.log("extract_action_items", "failed", f"JSON parse error: {e}. Raw: {raw[:300]}")
        state.status = "failed"
        return state

    state.log("extract_action_items", "success", f"Extracted {len(action_items)} action items")
    state.mark_step_done("extract_action_items")
    state.output["action_items_raw"] = action_items

    # ── Step 3: Classify — clear vs ambiguous ─────────────────────────────
    state.current_step = "classify_ownership"
    clear_items     = [i for i in action_items if not i.get("ambiguous") and i.get("owner")]
    ambiguous_items = [i for i in action_items if i.get("ambiguous") or not i.get("owner")]

    state.log(
        "classify_ownership", "success",
        f"{len(clear_items)} items with clear owners, {len(ambiguous_items)} ambiguous",
    )
    state.mark_step_done("classify_ownership")

    # ── Step 4: Flag ambiguous → request clarification ────────────────────
    if ambiguous_items:
        state.current_step = "flag_ambiguous"
        ambiguous_titles = [i["title"] for i in ambiguous_items]
        clarification_msg = (
            f"The following action items have no clear owner. "
            f"Please assign them before tasks can be created:\n"
            + "\n".join(f"  • {t}" for t in ambiguous_titles)
        )
        state.human_clarification_needed = clarification_msg
        state.log(
            "flag_ambiguous", "waiting_human",
            f"Flagged {len(ambiguous_items)} ambiguous items: {ambiguous_titles}",
        )
        # Notify via Slack
        await slack_send_message(
            channel="#project-updates",
            message=f"⚠️ *Meeting action items need owner assignment:*\n{clarification_msg}",
        )
        state.output["ambiguous_items"] = ambiguous_items
        state.mark_step_done("flag_ambiguous")

    # ── Step 5: Create JIRA tasks for clear items ─────────────────────────
    state.current_step = "create_jira_tasks"
    created_tasks = []
    for item in clear_items:
        try:
            task = await jira_create_task(
                title=item["title"],
                assignee=item["owner"],
                project=project,
            )
            created_tasks.append({**item, "jira": task})
            state.log(
                "create_jira_tasks", "success",
                f"Created {task['task_id']} — '{item['title']}' → {item['owner']}",
                "jira", str(task),
            )
        except Exception as e:
            state.log("create_jira_tasks", "failed", f"Failed to create task '{item['title']}': {e}")

    state.mark_step_done("create_jira_tasks")
    state.output["created_tasks"] = created_tasks

    # ── Step 6: Send summary email ─────────────────────────────────────────
    state.current_step = "send_summary_email"
    task_lines = "\n".join(
        f"  [{t['jira']['task_id']}] {t['title']} → {t['owner']}"
        for t in created_tasks
    )
    ambiguous_lines = (
        "\n⚠️ Items pending owner assignment:\n" +
        "\n".join(f"  • {i['title']}" for i in ambiguous_items)
    ) if ambiguous_items else ""

    body = f"""
Hi team,

Here's a summary of today's meeting action items:

✅ Tasks created in JIRA:
{task_lines or "  (none)"}
{ambiguous_lines}

Please review JIRA for full details.

— Meeting Intelligence Agent
""".strip()

    emails = [f"{p.lower().replace(' ', '.')}@company.com" for p in participants]
    result = await email_send(to=emails, subject="Meeting Action Items — Auto-generated", body=body)
    state.log("send_summary_email", "success", f"Summary sent to {emails}", "email", str(result))
    state.mark_step_done("send_summary_email")
    state.output["summary_email"] = result

    # ── Final ──────────────────────────────────────────────────────────────
    state.status = "waiting_human" if ambiguous_items else "success"
    return state
