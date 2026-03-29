"""
graph/orchestrator.py — LangGraph state machine (Module 1)

Defines the top-level graph that routes incoming scenarios to the correct
agent and wires in shared error handling + audit persistence.
"""
from __future__ import annotations
from typing import AsyncGenerator
import json

from langgraph.graph import StateGraph, END
from models.state import AgentState
from agents.onboarding import run_onboarding_agent
from agents.meeting    import run_meeting_agent
from agents.sla        import run_sla_agent


# ── Node wrappers (LangGraph nodes must return dicts) ──────────────────────

async def onboarding_node(state: dict) -> dict:
    s = AgentState(**state)
    result = await run_onboarding_agent(s)
    return result.model_dump()


async def meeting_node(state: dict) -> dict:
    s = AgentState(**state)
    result = await run_meeting_agent(s)
    return result.model_dump()


async def sla_node(state: dict) -> dict:
    s = AgentState(**state)
    result = await run_sla_agent(s)
    return result.model_dump()


# ── Router ─────────────────────────────────────────────────────────────────

def route_scenario(state: dict) -> str:
    scenario = state.get("scenario", "")
    if scenario == "onboarding":
        return "onboarding_agent"
    elif scenario == "meeting":
        return "meeting_agent"
    elif scenario == "sla":
        return "sla_agent"
    else:
        raise ValueError(f"Unknown scenario: {scenario}")


# ── Build the graph ────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    builder = StateGraph(dict)

    builder.add_node("onboarding_agent", onboarding_node)
    builder.add_node("meeting_agent",    meeting_node)
    builder.add_node("sla_agent",        sla_node)

    builder.set_conditional_entry_point(
        route_scenario,
        {
            "onboarding_agent": "onboarding_agent",
            "meeting_agent":    "meeting_agent",
            "sla_agent":        "sla_agent",
        },
    )

    builder.add_edge("onboarding_agent", END)
    builder.add_edge("meeting_agent",    END)
    builder.add_edge("sla_agent",        END)

    return builder.compile()


# Singleton compiled graph
GRAPH = build_graph()


# ── Streaming helper ───────────────────────────────────────────────────────

async def stream_agent_run(initial_state: AgentState) -> AsyncGenerator[str, None]:
    """
    Run the graph and yield Server-Sent Events as each audit log entry is appended.
    The frontend consumes this as a live step feed.
    """
    state_dict = initial_state.model_dump()
    seen_audit_count = 0

    async for chunk in GRAPH.astream(state_dict):
        # chunk is { node_name: state_dict }
        for node_name, node_state in chunk.items():
            audit_log = node_state.get("audit_log", [])
            # Yield only new entries since last chunk
            new_entries = audit_log[seen_audit_count:]
            seen_audit_count = len(audit_log)
            for entry in new_entries:
                yield f"data: {json.dumps({'type': 'step', 'entry': entry})}\n\n"

    # Yield final state summary
    final_state = await GRAPH.ainvoke(state_dict)  # gets final state
    yield f"data: {json.dumps({'type': 'complete', 'run_id': initial_state.run_id, 'status': final_state.get('status')})}\n\n"
