import { useEffect, useState } from 'react'
import ScenarioCard from '../components/ScenarioCard'
import { fetchRuns } from '../hooks/useAgentStream'

const STATUS_COLOR = {
  success:       '#22c55e',
  failed:        '#ef4444',
  escalated:     '#a855f7',
  waiting_human: '#f59e0b',
  running:       '#4f8ef7',
}

export default function Dashboard() {
  const [runs, setRuns]     = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchRuns().then(r => { setRuns(r); setLoading(false) }).catch(() => setLoading(false))
    const interval = setInterval(() => fetchRuns().then(setRuns).catch(() => {}), 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      {/* Header */}
      <header style={{
        borderBottom: '1px solid var(--border)',
        padding: '0 32px',
        height: 60,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        backdropFilter: 'blur(8px)',
        position: 'sticky', top: 0, zIndex: 10,
        background: 'rgba(8,11,16,0.9)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 6,
            background: 'linear-gradient(135deg, #4f8ef7, #7c5cfc)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 14,
          }}>◈</div>
          <span style={{ fontWeight: 800, fontSize: 15, letterSpacing: '-0.01em' }}>
            Enterprise Agent
          </span>
          <span style={{
            fontSize: 10, padding: '2px 8px', borderRadius: 3,
            background: 'rgba(79,142,247,0.15)', color: '#4f8ef7',
            fontFamily: 'var(--font-mono)',
          }}>ET GenAI Hackathon 2026</span>
        </div>
        <div style={{ display: 'flex', gap: 24, fontSize: 12, color: 'var(--muted)' }}>
          <span>LangGraph</span>
          <span>Groq · Llama 3.3 70B</span>
          <span>FastAPI</span>
        </div>
      </header>

      <main style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 32px' }}>
        {/* Hero */}
        <div style={{ marginBottom: 48 }}>
          <h1 style={{
            fontSize: 36, fontWeight: 800, letterSpacing: '-0.03em',
            lineHeight: 1.1, marginBottom: 12,
            background: 'linear-gradient(135deg, #e8edf5 40%, #6b7a92)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>
            Autonomous Enterprise<br />Workflow Agents
          </h1>
          <p style={{ color: 'var(--muted)', fontSize: 14, maxWidth: 520 }}>
            Multi-agent system with LangGraph orchestration, real error recovery,
            and full audit trails across three enterprise scenarios.
          </p>
        </div>

        {/* Metric strip */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 12, marginBottom: 40,
        }}>
          {[
            { label: 'Autonomy depth',    value: '7 steps',       color: '#4f8ef7' },
            { label: 'Error recovery',    value: 'retry → escalate', color: '#22c55e' },
            { label: 'Scenarios',         value: '3 live demos',  color: '#7c5cfc' },
            { label: 'Audit entries',     value: 'Full trail',    color: '#f59e0b' },
          ].map(m => (
            <div key={m.label} style={{
              background: 'var(--bg3)', border: '1px solid var(--border)',
              borderRadius: 10, padding: '16px 18px',
            }}>
              <div style={{ fontSize: 18, fontWeight: 800, color: m.color, marginBottom: 4 }}>{m.value}</div>
              <div style={{ fontSize: 11, color: 'var(--muted)' }}>{m.label}</div>
            </div>
          ))}
        </div>

        {/* Scenario cards */}
        <h2 style={{ fontSize: 13, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--muted)', marginBottom: 16 }}>
          SCENARIOS
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 48 }}>
          {['onboarding', 'meeting', 'sla'].map(s => (
            <ScenarioCard key={s} scenario={s} />
          ))}
        </div>

        {/* Recent runs */}
        {runs.length > 0 && (
          <>
            <h2 style={{ fontSize: 13, fontWeight: 700, letterSpacing: '0.08em', color: 'var(--muted)', marginBottom: 16 }}>
              RECENT RUNS
            </h2>
            <div style={{
              background: 'var(--bg2)', border: '1px solid var(--border)',
              borderRadius: 12, overflow: 'hidden',
            }}>
              {runs.slice().reverse().map((r, i) => {
                const color = STATUS_COLOR[r.status] || '#6b7a92'
                return (
                  <a key={r.run_id} href={`/run/${r.run_id}`} style={{
                    display: 'flex', alignItems: 'center', gap: 16,
                    padding: '14px 20px',
                    borderBottom: i < runs.length - 1 ? '1px solid var(--border)' : 'none',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <span style={{ color, fontSize: 16 }}>●</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)', flex: 1 }}>
                      {r.run_id.slice(0, 8)}
                    </span>
                    <span style={{ fontSize: 12, color: 'var(--text)', fontWeight: 600 }}>{r.scenario}</span>
                    <span style={{
                      fontSize: 11, color, background: `${color}18`,
                      padding: '2px 8px', borderRadius: 4, fontFamily: 'var(--font-mono)',
                    }}>{r.status}</span>
                    <span style={{ fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)' }}>
                      {r.steps_completed} steps
                    </span>
                    <span style={{ color: 'var(--muted)', fontSize: 12 }}>→</span>
                  </a>
                )
              })}
            </div>
          </>
        )}
      </main>
    </div>
  )
}
