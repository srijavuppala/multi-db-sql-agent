import { useEffect, useState } from 'react'
import { fetchSchema } from '../api/client'

const s = {
  panel: { width: 280, background: '#161b27', borderRight: '1px solid #2d3748', overflowY: 'auto', padding: '16px 12px', flexShrink: 0 },
  title: { fontSize: 13, fontWeight: 700, color: '#7c8db5', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 },
  dbName: { fontSize: 13, fontWeight: 600, color: '#63b3ed', marginBottom: 6, marginTop: 14 },
  pre: { fontSize: 11, color: '#a0aec0', whiteSpace: 'pre-wrap', lineHeight: 1.6 },
  error: { fontSize: 12, color: '#fc8181' },
}

export default function SchemaPanel() {
  const [schemas, setSchemas] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchSchema()
      .then(setSchemas)
      .catch(e => setError(e.message))
  }, [])

  return (
    <aside style={s.panel}>
      <div style={s.title}>Schema</div>
      {error && <div style={s.error}>{error}</div>}
      {schemas && Object.entries(schemas).map(([db, schema]) => (
        <div key={db}>
          <div style={s.dbName}>{db}</div>
          <pre style={s.pre}>{schema}</pre>
        </div>
      ))}
      {!schemas && !error && <div style={s.pre}>Loading…</div>}
    </aside>
  )
}
