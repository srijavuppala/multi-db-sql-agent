import ChatPanel from './components/ChatPanel'
import SchemaPanel from './components/SchemaPanel'
import { askQuestion } from './api/client'

const s = {
  app: { display: 'flex', height: '100vh', overflow: 'hidden' },
  header: { position: 'fixed', top: 0, left: 0, right: 0, height: 48, background: '#0f1117', borderBottom: '1px solid #2d3748', display: 'flex', alignItems: 'center', padding: '0 20px', zIndex: 10 },
  title: { fontSize: 15, fontWeight: 700, color: '#e2e8f0' },
  subtitle: { fontSize: 12, color: '#4a5568', marginLeft: 10 },
  body: { display: 'flex', flex: 1, marginTop: 48, overflow: 'hidden' },
}

export default function App() {
  return (
    <div style={s.app}>
      <header style={s.header}>
        <span style={s.title}>Multi-DB SQL Agent</span>
        <span style={s.subtitle}>sales_db · inventory_db</span>
      </header>
      <div style={s.body}>
        <SchemaPanel />
        <ChatPanel onAsk={askQuestion} />
      </div>
    </div>
  )
}
