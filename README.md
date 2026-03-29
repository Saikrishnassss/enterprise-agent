# 🤖 Enterprise Workflow Agent — ET GenAI Hackathon 2026

A **multi-agent autonomous system** built for Track 2: Autonomous Enterprise Workflows.
Three fully agentic scenarios, LangGraph orchestration, real error recovery, and a live audit trail.

---

## 🏗️ Architecture

```
React Dashboard (Vercel)
        ↓  REST / SSE
FastAPI Backend (Railway)
        ↓
LangGraph Orchestrator  ←→  SQLite Audit DB
        ↓
┌─────────────────────────────────┐
│  Onboarding  │ Meeting │  SLA   │  ← Scenario Agents
└─────────────────────────────────┘
        ↓
Shared Sub-Agents: Retrieval · Decision · Action · Verification · Escalation
        ↓
Mock Tool Layer: JIRA · Slack · Calendar · HR · Email · Approvals
        ↓
LLM: Groq (Llama 3.3 70B) — free tier
```

---

## 📦 Modules

| Module | Description |
|--------|-------------|
| `backend/graph/` | LangGraph state machine, retry logic, branching |
| `backend/agents/onboarding.py` | 7-step onboarding with JIRA error + IT escalation |
| `backend/agents/meeting.py` | Transcript → tasks, ambiguity flagging |
| `backend/agents/sla.py` | 48h breach detection, delegate reroute, audit |
| `backend/tools/` | Mock integrations: JIRA, Slack, Calendar, HR, Email |
| `backend/models/` | Pydantic state models + audit schema |
| `backend/api/` | FastAPI routes + SSE streaming |
| `frontend/src/` | React dashboard with live feed + audit log |

---

## 🚀 Quick Start

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                               # add your GROQ_API_KEY
uvicorn api.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local                        # set VITE_API_URL=http://localhost:8000
npm run dev
```

---

## 🔑 Environment Variables

### Backend `.env`
```
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=sqlite:///./audit.db
ENVIRONMENT=development
```

### Frontend `.env.local`
```
VITE_API_URL=http://localhost:8000
```

---

## 🌐 Deployment

| Service | Platform | Free Tier |
|---------|----------|-----------|
| Backend | Railway | ✅ 500 hrs/month |
| Frontend | Vercel | ✅ Unlimited |

See [`docs/deployment.md`](docs/deployment.md) for step-by-step instructions.

---

## 📊 Evaluation Alignment

| Dimension | How We Address It |
|-----------|-------------------|
| Autonomy Depth (30%) | 7 sequential steps in onboarding, auto-retry, auto-escalate |
| Multi-Agent Design (20%) | Orchestrator + 3 scenario agents + 5 shared sub-agents |
| Technical Creativity (20%) | LangGraph state machine, SSE live feed, model routing |
| Enterprise Readiness (20%) | Full audit trail, graceful degradation, compliance guards |
| Impact Quantification (10%) | Onboarding: saves ~4hrs/hire; SLA: prevents breach costs |

---

## 📁 Repo Structure

```
enterprise-agent/
├── backend/
│   ├── agents/          # Scenario-specific agent logic
│   ├── graph/           # LangGraph orchestrator
│   ├── tools/           # Mock tool integrations
│   ├── models/          # Pydantic state + audit models
│   ├── api/             # FastAPI app + routes
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/  # AgentFeed, AuditLog, ScenarioCard
│   │   ├── pages/       # Dashboard, ScenarioDetail
│   │   └── hooks/       # useAgentStream, useAuditLog
│   ├── package.json
│   └── .env.example
└── docs/
    └── deployment.md
```
