import { useEffect, useRef, useState } from 'react'
import SqlDisplay from './SqlDisplay'

const s = {
  panel: { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  messages: { flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 },
  bubble: { maxWidth: '80%', padding: '12px 16px', borderRadius: 12, lineHeight: 1.6, fontSize: 14 },
  user: { alignSelf: 'flex-end', background: '#2b4a7a', color: '#e2e8f0' },
  assistant: { alignSelf: 'flex-start', background: '#1e2a3a', color: '#e2e8f0', maxWidth: '90%' },
  dbBadge: { display: 'inline-block', fontSize: 10, background: '#2d3748', color: '#7c8db5', borderRadius: 4, padding: '2px 7px', marginBottom: 6, marginRight: 4 },
  error: { color: '#fc8181', fontSize: 13 },
  form: { padding: '16px 24px', borderTop: '1px solid #2d3748', display: 'flex', gap: 10 },
  input: { flex: 1, background: '#1a2035', border: '1px solid #2d3748', borderRadius: 8, padding: '10px 14px', color: '#e2e8f0', fontSize: 14, outline: 'none' },
  btn: { background: '#2b4a7a', color: '#e2e8f0', border: 'none', borderRadius: 8, padding: '10px 20px', cursor: 'pointer', fontSize: 14, fontWeight: 600 },
  btnDisabled: { opacity: 0.5, cursor: 'not-allowed' },
  thinking: { color: '#7c8db5', fontSize: 13, fontStyle: 'italic' },
}

function Message({ msg }) {
  if (msg.role === 'user') {
    return <div style={{ ...s.bubble, ...s.user }}>{msg.text}</div>
  }
  if (msg.loading) {
    return <div style={{ ...s.bubble, ...s.assistant }}><span style={s.thinking}>Thinking…</span></div>
  }
  return (
    <div style={{ ...s.bubble, ...s.assistant }}>
      {msg.db_targets?.map(db => <span key={db} style={s.dbBadge}>{db}</span>)}
      {msg.error
        ? <div style={s.error}>Error: {msg.error}</div>
        : <div>{msg.text}</div>
      }
      <SqlDisplay sql={msg.sql} sqlByDb={msg.sql_by_db} />
    </div>
  )
}

const EXAMPLES = [
  'How many customers are there?',
  'Show me the top 5 customers by total revenue',
  'Which products are low on stock?',
  'Which customers ordered products that are low on stock?',
]

export default function ChatPanel({ onAsk }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function submit(question) {
    if (!question.trim() || loading) return
    const q = question.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: q }, { role: 'assistant', loading: true }])
    setLoading(true)
    try {
      const data = await onAsk(q)
      setMessages(prev => [
        ...prev.slice(0, -1),
        {
          role: 'assistant',
          text: data.final_answer,
          sql: data.sql,
          sql_by_db: data.sql_by_db,
          db_targets: data.db_targets,
          error: data.error,
        },
      ])
    } catch (e) {
      setMessages(prev => [...prev.slice(0, -1), { role: 'assistant', error: e.message, text: '' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={s.panel}>
      <div style={s.messages}>
        {messages.length === 0 && (
          <div style={{ color: '#4a5568', fontSize: 13, marginTop: 20 }}>
            <div style={{ marginBottom: 12, color: '#7c8db5' }}>Try asking:</div>
            {EXAMPLES.map(ex => (
              <div
                key={ex}
                onClick={() => submit(ex)}
                style={{ cursor: 'pointer', marginBottom: 8, padding: '6px 10px', borderRadius: 6, background: '#161b27', color: '#90cdf4' }}
              >
                {ex}
              </div>
            ))}
          </div>
        )}
        {messages.map((m, i) => <Message key={i} msg={m} />)}
        <div ref={bottomRef} />
      </div>
      <form style={s.form} onSubmit={e => { e.preventDefault(); submit(input) }}>
        <input
          style={s.input}
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask a question about your data…"
          disabled={loading}
        />
        <button style={{ ...s.btn, ...(loading ? s.btnDisabled : {}) }} type="submit" disabled={loading}>
          Ask
        </button>
      </form>
    </div>
  )
}
