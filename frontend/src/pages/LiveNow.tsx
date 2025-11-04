import { useEffect, useMemo, useState } from 'react'
import { api } from '@/lib/api'

type HealthPayload = any

const LiveNow = () => {
  const apiBase = useMemo(() => import.meta.env.VITE_API_URL || 'http://localhost:9000', [])
  const backendProd = 'https://omni-ultra-backend-prod-661612368188.europe-west1.run.app'
  const docsUrl = `${backendProd}/api/docs`
  const [healthApi, setHealthApi] = useState<'ok' | 'fail' | 'loading'>('loading')
  const [healthGateway, setHealthGateway] = useState<'ok' | 'fail' | 'loading'>('loading')
  const [summary, setSummary] = useState<HealthPayload | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const run = async () => {
      setError(null)
      setHealthApi('loading')
      setHealthGateway('loading')
      try {
        // Try FastAPI health (backend)
        const resApi = await api.get('/api/health')
        setHealthApi(resApi?.data?.status ? 'ok' : 'fail')
      } catch (e: any) {
        setHealthApi('fail')
      }
      try {
        // Try Gateway health (/healthz)
        const resGw = await api.get('/healthz')
        setHealthGateway(resGw?.data?.status === 'ok' ? 'ok' : 'fail')
      } catch {
        setHealthGateway('fail')
      }
      try {
        const resSummary = await api.get('/api/v1/omni/summary')
        setSummary(resSummary.data)
      } catch (e: any) {
        setError(e?.message || 'Ni povzetka sistema')
      }
    }
    run()
  }, [])

  const Badge = ({ state, label }: { state: 'ok' | 'fail' | 'loading', label: string }) => (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 10px',
      borderRadius: 12, fontSize: 12,
      background: state === 'ok' ? 'rgba(0,255,136,0.12)' : state === 'loading' ? 'rgba(255,221,0,0.12)' : 'rgba(255,85,85,0.12)',
      border: state === 'ok' ? '1px solid rgba(0,255,136,0.35)' : state === 'loading' ? '1px solid rgba(255,221,0,0.35)' : '1px solid rgba(255,85,85,0.35)'
    }}>
      <span style={{ width: 8, height: 8, borderRadius: '50%', background: state === 'ok' ? '#00ff88' : state === 'loading' ? '#ffdd00' : '#ff5555' }} />
      <span>{label}</span>
    </div>
  )

  const openWindow = (url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: 24 }}>
      <h1 className="gradient-text" style={{ fontSize: 36, marginBottom: 8 }}>What’s Live Now</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>Vse ključne povezave, statusi in hitri testi v enem pogledu.</p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 16 }}>
        <div className="card">
          <h2 style={{ fontSize: 20, marginBottom: 12 }}>Backend ML Service</h2>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
            <Badge state={healthApi} label={healthApi === 'ok' ? 'API /api/health OK' : healthApi === 'loading' ? 'Preverjam…' : 'API nedosegljiv'} />
            <Badge state={healthGateway} label={healthGateway === 'ok' ? 'Gateway /healthz OK' : healthGateway === 'loading' ? 'Preverjam…' : 'Gateway nedosegljiv'} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div><strong>Prod URL:</strong> <code>{backendProd}</code></div>
            <div><strong>Frontend API_BASE:</strong> <code>{apiBase}</code></div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
              <button onClick={() => openWindow(`${backendProd}/api/health`)} className="btn btn-secondary">Odpri /api/health</button>
              <button onClick={() => openWindow(docsUrl)} className="btn btn-secondary">Odpri /api/docs</button>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 style={{ fontSize: 20, marginBottom: 12 }}>Dashboard Builder (Ollama)</h2>
          <p style={{ marginBottom: 12 }}>AI generira 20 React TS dashboardov. Na voljo status, seznam tipov in build.</p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button onClick={() => openWindow(`${apiBase}/api/v1/dashboards/build/status`)} className="btn btn-secondary">Status Builder</button>
            <button onClick={() => openWindow(`${apiBase}/api/v1/dashboards/types`)} className="btn btn-secondary">Seznam tipov</button>
            <button onClick={() => openWindow(`${apiBase}/api/v1/dashboards/build`)} className="btn btn-secondary">Build (POST)</button>
          </div>
          <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-secondary)' }}>
            PS: <code>.\\build-dashboards.ps1 -Action build-priority -Priority 1 -Url {apiBase}</code>
          </div>
        </div>

        <div className="card">
          <h2 style={{ fontSize: 20, marginBottom: 12 }}>Grafana Monitoring</h2>
          <p style={{ marginBottom: 12 }}>Prometheus integracija: cache, FastAPI, business KPI. Uporabi pripravljene dashboarde.</p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button onClick={() => openWindow('http://localhost:3000')} className="btn btn-secondary">Lok. Grafana (če je zagnana)</button>
            <button onClick={() => openWindow(`${apiBase}/metrics`)} className="btn btn-secondary">Gateway /metrics</button>
          </div>
        </div>

        <div className="card">
          <h2 style={{ fontSize: 20, marginBottom: 12 }}>AI/ML Endpoints (hitri testi)</h2>
          <div style={{ display: 'grid', gap: 8 }}>
            <button onClick={() => openWindow(`${apiBase}/api/v1/ai/sentiment?text=To%20je%20odli%C4%8Dno!`)} className="btn btn-secondary">Sentiment GET</button>
            <button onClick={() => openWindow(`${apiBase}/api/v1/intelligence/revenue/predict?months=3`)} className="btn btn-secondary">Revenue Predict</button>
            <button onClick={() => openWindow(`${apiBase}/api/v1/omni/summary`)} className="btn btn-secondary">System Summary</button>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h2 style={{ fontSize: 20, marginBottom: 12 }}>Napake / Povzetek</h2>
        {error ? (
          <div style={{ color: '#ff5555' }}>{error}</div>
        ) : (
          <pre style={{ maxHeight: 260, overflow: 'auto', background: 'rgba(255,255,255,0.04)', padding: 12, borderRadius: 8 }}>
            {JSON.stringify(summary, null, 2)}
          </pre>
        )}
      </div>
    </div>
  )
}

export default LiveNow