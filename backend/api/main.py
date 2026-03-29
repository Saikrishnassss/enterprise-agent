"""
api/main.py — FastAPI application (Module 5)

Routes:
  POST /run          — trigger a scenario, returns run_id
  GET  /stream/{id}  — SSE stream of agent steps for a given run
  GET  /audit/{id}   — fetch full audit log for a completed run
  GET  /health       — health check
"""
import os
import json
import asyncio
from typing import Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from models.state import AgentState, ScenarioType
from graph.orchestrator import GRAPH, stream_agent_run

# In-memory run store (swap for Redis in production)
RUN_STORE: dict[str, AgentState] = {}
STREAM_QUEUES: dict[str, asyncio.Queue] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ Enterprise Agent API starting...")
    yield
    print("🛑 Enterprise Agent API shutting down.")


app = FastAPI(
    title="Enterprise Workflow Agent API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ──────────────────────────────────────────────

class RunRequest(BaseModel):
    scenario: ScenarioType
    payload: dict[str, Any] = {}


class RunResponse(BaseModel):
    run_id: str
    scenario: ScenarioType
    status: str


# ── Demo payloads (used when payload is empty) ─────────────────────────────

DEMO_PAYLOADS: dict[str, dict] = {
    "onboarding": {
        "employee_id": "EMP-2026-042",
        "name": "Aditya Kumar",
        "department": "Engineering",
        "manager_id": "EMP005",
        "buddy_id": "EMP003",
    },
    "meeting": {
        "transcript": """
Priya: Alright, let's wrap up. Arjun, can you handle the API documentation by Friday?
Arjun: Sure, I'll take that.
Priya: Great. Kavya, what about the design review?
Kavya: I can do that by end of week.
Priya: And we need someone to update the roadmap — it's been outdated for a month.
Arjun: I think that should go to whoever owns the product vision... not sure who that is now.
Priya: We'll figure it out. Also, the server migration — Arjun, is your team on that?
Arjun: Yes, we're targeting next Wednesday.
Priya: Perfect. Let's also schedule a retrospective — maybe Kavya can set that up?
Kavya: Done.
""",
        "participants": ["Priya Sharma", "Arjun Mehta", "Kavya Reddy", "Rahul Verma"],
        "jira_project": "ENG",
    },
    "sla": {},
}


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/run", response_model=RunResponse)
async def trigger_run(req: RunRequest):
    payload = req.payload or DEMO_PAYLOADS.get(req.scenario, {})
    state = AgentState(scenario=req.scenario, input_payload=payload)
    RUN_STORE[state.run_id] = state
    STREAM_QUEUES[state.run_id] = asyncio.Queue()

    # Run agent in background
    asyncio.create_task(_execute_run(state))

    return RunResponse(run_id=state.run_id, scenario=req.scenario, status="running")


async def _execute_run(state: AgentState):
    """Execute agent run and push SSE events to the run's queue."""
    queue = STREAM_QUEUES[state.run_id]
    seen_audit = 0

    try:
        state_dict = state.model_dump()
        final_state_dict = await GRAPH.ainvoke(state_dict)
        final = AgentState(**final_state_dict)
        RUN_STORE[state.run_id] = final

        # Push all audit entries to the queue
        for entry in final.audit_log[seen_audit:]:
            await queue.put({"type": "step", "entry": entry.model_dump()})

        await queue.put({
            "type": "complete",
            "run_id": state.run_id,
            "status": final.status,
            "steps_completed": final.steps_completed,
            "escalation_required": final.escalation_required,
            "human_clarification_needed": final.human_clarification_needed,
        })
    except Exception as e:
        await queue.put({"type": "error", "run_id": state.run_id, "error": str(e)})
    finally:
        await queue.put(None)  # sentinel


@app.get("/stream/{run_id}")
async def stream_run(run_id: str):
    if run_id not in STREAM_QUEUES:
        raise HTTPException(404, "Run not found")

    queue = STREAM_QUEUES[run_id]

    async def event_generator():
        while True:
            item = await asyncio.wait_for(queue.get(), timeout=120)
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/audit/{run_id}")
async def get_audit(run_id: str):
    if run_id not in RUN_STORE:
        raise HTTPException(404, "Run not found")
    state = RUN_STORE[run_id]
    return {
        "run_id": run_id,
        "scenario": state.scenario,
        "status": state.status,
        "steps_completed": state.steps_completed,
        "audit_log": [e.model_dump() for e in state.audit_log],
        "output": state.output,
        "escalation_required": state.escalation_required,
        "human_clarification_needed": state.human_clarification_needed,
    }


@app.get("/runs")
async def list_runs():
    return [
        {
            "run_id": s.run_id,
            "scenario": s.scenario,
            "status": s.status,
            "steps_completed": len(s.steps_completed),
        }
        for s in RUN_STORE.values()
    ]
