# Deployment Guide

## Backend → Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **New Project → Deploy from GitHub repo**
3. Select this repo, set **Root Directory** to `backend`
4. Railway auto-detects Python. Set the **Start Command**:
   ```
   uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```
5. Add environment variables in Railway dashboard:
   ```
   GROQ_API_KEY=your_key_here
   DATABASE_URL=sqlite:///./audit.db
   ENVIRONMENT=production
   CORS_ORIGINS=https://your-app.vercel.app
   ```
6. Deploy. Railway gives you a URL like `https://enterprise-agent-backend.up.railway.app`

---

## Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click **Add New → Project**, import this repo
3. Set **Root Directory** to `frontend`
4. Set **Framework Preset** to `Vite`
5. Add environment variable:
   ```
   VITE_API_URL=https://your-backend.up.railway.app
   ```
6. Deploy. Vercel gives you a URL like `https://enterprise-agent.vercel.app`

---

## Update CORS

After frontend is deployed, go back to Railway and update:
```
CORS_ORIGINS=https://enterprise-agent.vercel.app
```
Redeploy the backend.

---

## Get a Free Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free, no credit card needed)
3. Create an API key
4. Add it to Railway as `GROQ_API_KEY`

Groq free tier: 14,400 requests/day on Llama 3.3 70B — more than enough for demos.

---

## Local Development

```bash
# Terminal 1 — Backend
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # add GROQ_API_KEY
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open http://localhost:5173
