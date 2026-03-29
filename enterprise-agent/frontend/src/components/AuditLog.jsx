const STATUS_COLOR = {
  success:       '#22c55e',
  failed:        '#ef4444',
  escalated:     '#a855f7',
  waiting_human: '#f59e0b',
  running:       '#4f8ef7',
}

export default function AuditLog({ entries = [] }) {
  if (!entries.length) return null

  return (
    <div style={{
      background: 'var(--bg2)',
      border: '1px solid var(--border)',
      borderRadius: 12,
      overflow: 'hidden',
    }}>
      <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)' }}>
        <span style={{ fontSize: 12, fontWeight: 700, letterSpacing: '0.08em' }}>AUDIT TRAIL</span>
        <span style={{ marginLeft: 8, fontSize: 11, color: 'var(--muted)', fontFamily: 'var(--font-mono)' }}>
          {entries.length} entries
        </span>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              {['Time', 'Step', 'Status', 'Tool', 'Detail'].map(h => (
                <th key={h} style={{
                  padding: '8px 14px', textAlign: 'left',
                  color: 'var(--muted)', fontWeight: 600,
                  fontSize: 11, letterSpacing: '0.06em',
                  whiteSpace: 'nowrap',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {entries.map((e, i) => {
              const color = STATUS_COLOR[e.status] || '#6b7a92'
              return (
                <tr key={i} style={{
                  borderBottom: '1px solid var(--border)',
                  background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.015)',
                }}>
                  <td style={{ padding: '8px 14px', fontFamily: 'var(--font-mono)', color: 'var(--muted)', whiteSpace: 'nowrap' }}>
                    {new Date(e.timestamp).toLocaleTimeString()}
                  </td>
                  <td style={{ padding: '8px 14px', fontFamily: 'var(--font-mono)', color: 'var(--text)', whiteSpace: 'nowrap' }}>
                    {e.step.replace(/_/g, ' ')}
                  </td>
                  <td style={{ padding: '8px 14px' }}>
                    <span style={{
                      color, background: `${color}18`,
                      padding: '2px 7px', borderRadius: 4,
                      fontSize: 11, fontFamily: 'var(--font-mono)',
                    }}>{e.status}</span>
                  </td>
                  <td style={{ padding: '8px 14px', fontFamily: 'var(--font-mono)', color: '#4f8ef7', fontSize: 11 }}>
                    {e.tool_called || '—'}
                  </td>
                  <td style={{ padding: '8px 14px', color: 'var(--muted)', maxWidth: 320 }}>
                    <span style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {e.detail}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
