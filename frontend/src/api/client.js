const BASE = ''  // proxied to http://localhost:8000 by Vite

export async function askQuestion(question) {
  const res = await fetch(`${BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export async function fetchSchema() {
  const res = await fetch(`${BASE}/schema`)
  if (!res.ok) throw new Error('Failed to fetch schema')
  return res.json()
}
