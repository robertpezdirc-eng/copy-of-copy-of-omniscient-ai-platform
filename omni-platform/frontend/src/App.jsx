import { useEffect, useState } from 'react'
import brand from './config/brand_config.json'
import logoUrl from '../public/logo.svg?url'
import OmniChatDashboard from './components/OmniChatDashboard'
import AdminDashboard from './components/AdminDashboard'

const backendBase = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_URL || ''

export default function App() {
  const [healthJson, setHealthJson] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const base = backendBase || ''
    const hurl = `${base}/api/health`
    fetch(hurl)
      .then(res => res.text().then(t => {
        try { setHealthJson(JSON.parse(t)) } catch { setHealthJson({ raw: t, status: res.status }) }
      }))
      .catch(e => setError(prev => (prev ? prev + '\n' : '') + `Health error: ${e.message}`))
  }, [])

  return (
    <div className="app" style={{
      '--primary': brand.primary_color,
      '--secondary': brand.secondary_color,
      '--accent': brand.accent_color,
    }}>
      <header className="header">
        <img src={logoUrl} alt={brand.brand_name} className="logo" />
        <h1>{brand.brand_name}</h1>
      </header>

      <main className="content">
        <section className="card" style={{padding: 0}}>
          <h3 style={{margin: '16px'}}>Klepetalni vmesnik</h3>
          <OmniChatDashboard />
        </section>

        <section className="card">
          <h3>Admin Dashboard</h3>
          <AdminDashboard />
        </section>

        <section className="card">
          <h3>API Health (JSON)</h3>
          <pre style={{whiteSpace: 'pre-wrap'}}>{healthJson ? JSON.stringify(healthJson, null, 2) : 'Loading...'}</pre>
          {error && <p style={{color: 'red'}}>{error}</p>}
        </section>
      </main>

      <footer className="footer">
        <small>&copy; {new Date().getFullYear()} {brand.seo?.site_name || brand.brand_name}</small>
      </footer>
    </div>
  )
}