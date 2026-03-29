import { useState, useEffect, useRef } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function useAgentStream(runId) {
  const [steps, setSteps]         = useState([])
  const [complete, setComplete]   = useState(null)
  const [error, setError]         = useState(null)
  const [streaming, setStreaming] = useState(false)
  const esRef = useRef(null)

  useEffect(() => {
    if (!runId) return
    setSteps([])
    setComplete(null)
    setError(null)
    setStreaming(true)

    const es = new EventSource(`${API}/stream/${runId}`)
    esRef.current = es

    es.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'step') {
        setSteps(prev => [...prev, data.entry])
      } else if (data.type === 'complete') {
        setComplete(data)
        setStreaming(false)
        es.close()
      } else if (data.type === 'error') {
        setError(data.error)
        setStreaming(false)
        es.close()
      }
    }

    es.onerror = () => {
      setStreaming(false)
      es.close()
    }

    return () => { es.close() }
  }, [runId])

  return { steps, complete, error, streaming }
}

export async function triggerRun(scenario, payload = {}) {
  const res = await fetch(`${API}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario, payload }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function fetchAudit(runId) {
  const res = await fetch(`${API}/audit/${runId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function fetchRuns() {
  const res = await fetch(`${API}/runs`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
