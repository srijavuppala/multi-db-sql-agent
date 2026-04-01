const s = {
  box: { background: '#1a2035', border: '1px solid #2d3748', borderRadius: 8, padding: '12px 14px', marginTop: 10 },
  label: { fontSize: 11, color: '#7c8db5', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 },
  pre: { fontSize: 12, color: '#90cdf4', whiteSpace: 'pre-wrap', margin: 0 },
  dbTag: { display: 'inline-block', fontSize: 10, background: '#2b4a7a', color: '#90cdf4', borderRadius: 4, padding: '1px 6px', marginBottom: 4 },
}

export default function SqlDisplay({ sql, sqlByDb }) {
  if (!sql && !sqlByDb) return null

  if (sqlByDb && Object.keys(sqlByDb).length > 0) {
    return (
      <div style={s.box}>
        <div style={s.label}>SQL Generated</div>
        {Object.entries(sqlByDb).map(([db, q]) => (
          <div key={db} style={{ marginBottom: 8 }}>
            <span style={s.dbTag}>{db}</span>
            <pre style={s.pre}>{q}</pre>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div style={s.box}>
      <div style={s.label}>SQL Generated</div>
      <pre style={s.pre}>{sql}</pre>
    </div>
  )
}
