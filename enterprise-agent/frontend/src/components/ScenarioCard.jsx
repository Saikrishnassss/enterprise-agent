import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { triggerRun } from '../hooks/useAgentStream'

const SCENARIOS = [
  {
    id: 'onboarding',
    label: 'Employee Onboarding',
    icon: '◈',
    color: '#4f8ef7',
    tag: '7 steps · error recovery · IT escalation',
    desc: 'New hire joins Monday. Agent creates accounts across 3 systems, assigns buddy, schedules orientation. JIRA fails mid-flow — retry then escalate.',
  },
  {
    id: 'meeting',
    label: 'Meeting → Action',
    icon: '◉',
    color: '#7c5cfc',
    tag: 'LLM extraction · ambiguity flag · JIRA tasks',
    desc: 'Transcript with 4 participants. Extract action items, assign owners by context, create JIRA tasks, flag ambiguous ownership for clarification.',
  },
  {
    id: 'sla',
    label: 'SLA Breach Prevention',
    icon: '◆',
    color: '#f59e0b',
    tag: '48h breach · delegate reroute · audit trail',
    desc: 'Procurement approval stuck 48h. Detect bottleneck (approver on leave), reroute to delegate, log compliance override.',
  },
]

export default function ScenarioCard({ scenario }) {
  const s = SCENARIOS.find(x => x.id === scenario) || SCENARIOS[0]
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleRun() {
    setLoading(true)
    try {
      const { run_id } = await triggerRun(s.id)
      navigate(`/run/${run_id}?scenario=${s.id}`)
    } catch (e) {
      alert('Failed to start run: ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      background: 'var(--bg3)',
      border: `1px solid var(--border2)`,
      borderTop: `2px solid ${s.color}`,
      borderRadius: 12,
      padding: '24px',
      display: 'flex',
      flexDirection: 'column',
      gap: 12,
      transition: 'transform 0.15s',
    }}
    onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
    onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 22, color: s.color }}>{s.icon}</span>
        <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)' }}>{s.label}</span>
      </div>
      <span style={{
        fontSize: 11, fontFamily: 'var(--font-mono)',
        color: s.color, background: `${s.color}18`,
        padding: '3px 8px', borderRadius: 4, alignSelf: 'flex-start',
      }}>{s.tag}</span>
      <p style={{ color: 'var(--muted)', fontSize: 13, lineHeight: 1.6 }}>{s.desc}</p>
      <button
        onClick={handleRun}
        disabled={loading}
        style={{
          marginTop: 8,
          background: loading ? 'var(--bg2)' : s.color,
          color: loading ? 'var(--muted)' : '#fff',
          border: loading ? '1px solid var(--border2)' : 'none',
          borderRadius: 8,
          padding: '10px 0',
          fontWeight: 700,
          fontSize: 13,
          fontFamily: 'var(--font-ui)',
          letterSpacing: '0.02em',
          transition: 'opacity 0.15s',
        }}
      >
        {loading ? 'Starting…' : '▶  Run Demo'}
      </button>
    </div>
  )
}
