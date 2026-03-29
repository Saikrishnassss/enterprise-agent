import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAgentStream, fetchAudit } from '../hooks/useAgentStream'
import AgentFeed from '../components/AgentFeed'
import AuditLog  from '../components/AuditLog'

const STATUS_COLOR = {
  success:       '#22c55e',
  failed:        '#ef4444',
  escalated:     '#a855f7',
  waiting_human: '#f59e0b',
  running:       '#4f8ef7',
}

export default function RunDetail() {
  const { id }               = useParams()
  const [params]             = useSearchParams()
  const navigate             = useNavigate()
  const scenario             = params.get('scenario') || '—'
  const { steps, complete, error, streaming } = useAgentStream(id)
  const [audit, setAudit]    = useState(null)

  useEffect(() => {
    if (complete) {
      fetchAudit(id).then(setAudit).catch(() => {})
    }
  }, [complete, id])

  const statusColor = complete ? (STATUS_COLOR[complete.status] || '#6b7a92') : '#4f8ef7'

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      {/* Header */}
      <header style={{
        borderBottom: '1px solid var(--border)',
        padding: '0 32px',
        height: 60,
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        background: 'rgba(8,11,16,0.9)',
        position: 'sticky', top: 0, zIndex: 10,
      }}>
        <button onClick={() => navigate('/')} style={{
          background: 'var(--bg3)', border: '1px solid var(--border)',
          color: 'var(--muted)', borderRadius: 6, padding: '6px 12px',
          fontSize: 12, fontFamily: 'var(--font-ui)',
        }}>← Back</button>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--muted)' }}>
          {id?.slice(0, 8)}
        </span>
        <span style={{
          fontSize: 13, fontWeight: 700, color: 'var(--text)',
          textTransform: 'capitalize',
        }}>{scenario}</span>
        {streaming && (
          <span style={{
            fontSize: 11, color: '#22c55e', fontFamily: 'var(--font-mono)',
            display: 'flex', alignItems: 'center', gap: 4,
          }}>
            <span>●</span> running
          </span>
        )}
        {complete && (
          <span style={{
            fontSize: 11, color: statusColor, fontFamily: 'var(--font-mono)',
            background: `${statusColor}18`, padding: '3px 8px', borderRadius: 4,
          }}>
            ● {complete.status}
          </span>
        )}
      </header>

      <main style={{ maxWidth: 900, margin: '0 auto', padding: '32px 32px' }}>
        {/* Summary banner after complete */}
        {complete && (
          <div style={{
            background: `${statusColor}10`,
            border: `1px solid ${statusColor}40`,
            borderRadius: 10, padding: '16px 20px',
            marginBottom: 24,
            display: 'flex', alignItems: 'flex-start', gap: 16,
          }}>
            <span style={{ fontSize: 24, color: statusColor }}>
              {complete.status === 'success' ? '✓' : complete.status === 'escalated' ? '⬆' : complete.status === 'waiting_human' ? '?' : '✗'}
            </span>
            <div>
              <div style={{ fontWeight: 700, color: statusColor, marginBottom: 4 }}>
                {complete.status === 'success'       && 'All steps completed successfully'}
                {complete.status === 'escalated'     && 'Escalated to human — see audit trail'}
                {complete.status === 'waiting_human' && 'Awaiting human clarification'}
                {complete.status === 'failed'        && 'Run failed — see audit trail'}
              </div>
              <div style={{ fontSize: 12, color: 'var(--muted)' }}>
                {complete.steps_completed?.length} steps completed
                {complete.human_clarification_needed && (
                  <span style={{ color: '#f59e0b', marginLeft: 12 }}>
                    ⚠ {complete.human_clarification_needed}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {error && (
          <div style={{
            background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)',
            borderRadius: 10, padding: '16px 20px', marginBottom: 24,
            color: '#ef4444', fontSize: 13,
          }}>
            ✗ Error: {error}
          </div>
        )}

        {/* Live feed */}
        <div style={{ marginBottom: 24 }}>
          <AgentFeed steps={steps} streaming={streaming} complete={complete} />
        </div>

        {/* Full audit table */}
        {audit && <AuditLog entries={audit.audit_log} />}
      </main>
    </div>
  )
}
