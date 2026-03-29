import { useEffect, useRef } from 'react'

const STATUS_COLOR = {
  running:       '#4f8ef7',
  success:       '#22c55e',
  failed:        '#ef4444',
  escalated:     '#a855f7',
  waiting_human: '#f59e0b',
  pending:       '#6b7a92',
}

const STATUS_ICON = {
  running:       '◌',
  success:       '✓',
  failed:        '✗',
  escalated:     '⬆',
  waiting_human: '?',
  pending:       '○',
}

function StepRow({ entry, index }) {
  const color = STATUS_COLOR[entry.status] || '#6b7a92'
  const icon  = STATUS_ICON[entry.status]  || '·'

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '28px 1fr',
      gap: 0,
      animation: 'fadeIn 0.25s ease',
    }}>
      {/* Left spine */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <div style={{
          width: 24, height: 24, borderRadius: '50%',
          background: `${color}18`, border: `1.5px solid ${color}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 11, color, fontWeight: 700, flexShrink: 0,
          fontFamily: 'var(--font-mono)',
        }}>{icon}</div>
        <div style={{ width: 1, flex: 1, background: 'var(--border)', minHeight: 12 }} />
      </div>

      {/* Content */}
      <div style={{ paddingLeft: 12, paddingBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color, fontWeight: 500 }}>
            {entry.step.replace(/_/g, ' ')}
          </span>
          <span style={{
            fontSize: 10, padding: '1px 6px', borderRadius: 3,
            background: `${color}18`, color, fontFamily: 'var(--font-mono)',
          }}>{entry.status}</span>
          {entry.retry_count > 0 && (
            <span style={{ fontSize: 10, color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>
              retry #{entry.retry_count}
            </span>
          )}
        </div>
        <p style={{ color: 'var(--muted)', fontSize: 12, marginBottom: entry.tool_called ? 6 : 0 }}>
          {entry.detail}
        </p>
        {entry.tool_called && (
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            background: 'var(--bg2)', border: '1px solid var(--border)',
            borderRadius: 4, padding: '3px 8px', marginTop: 4,
          }}>
            <span style={{ color: 'var(--muted)', fontSize: 10 }}>tool</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#4f8ef7' }}>
              {entry.tool_called}
            </span>
          </div>
        )}
        {entry.escalated_to && (
          <div style={{
            marginTop: 6, fontSize: 11, color: '#a855f7',
            fontFamily: 'var(--font-mono)',
          }}>⬆ escalated → {entry.escalated_to}</div>
        )}
        <div style={{ fontSize: 10, color: 'var(--border2)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
          {new Date(entry.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}

export default function AgentFeed({ steps, streaming, complete }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [steps.length])

  return (
    <div style={{
      background: 'var(--bg2)',
      border: '1px solid var(--border)',
      borderRadius: 12,
      padding: '20px 20px 8px',
      minHeight: 200,
      maxHeight: 520,
      overflowY: 'auto',
    }}>
      <style>{`@keyframes fadeIn { from { opacity:0; transform:translateY(6px) } to { opacity:1; transform:translateY(0) } }`}</style>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text)', letterSpacing: '0.08em' }}>
          AGENT FEED
        </span>
        {streaming && (
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            fontSize: 10, color: '#22c55e', fontFamily: 'var(--font-mono)',
          }}>
            <span style={{ animation: 'pulse 1s infinite' }}>●</span> live
          </span>
        )}
        {complete && (
          <span style={{
            fontSize: 10, color: STATUS_COLOR[complete.status] || '#6b7a92',
            fontFamily: 'var(--font-mono)',
          }}>
            ● {complete.status}
          </span>
        )}
      </div>

      {steps.length === 0 && !streaming && (
        <p style={{ color: 'var(--muted)', fontSize: 12, textAlign: 'center', padding: '40px 0' }}>
          Run a scenario to see the agent work in real time.
        </p>
      )}

      {steps.map((step, i) => (
        <StepRow key={step.id || i} entry={step} index={i} />
      ))}

      {streaming && (
        <div style={{ display: 'flex', gap: 4, padding: '8px 0 12px 40px' }}>
          {[0, 150, 300].map(d => (
            <span key={d} style={{
              width: 6, height: 6, borderRadius: '50%', background: '#4f8ef7',
              animation: `pulse 1.2s ${d}ms infinite`,
            }} />
          ))}
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
