import { useEffect, useState } from 'react'
import brand from './config/brand_config.json'
import logoUrl from '../public/logo.svg?url'
import { api } from './api/client'

export default function App() {
  const [health, setHealth] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    // Example API call to Cloud Run / omni API (health endpoint)
    api.get('/health').then((res) => setHealth(res.ok ? 'OK' : 'Napaka')).catch(() => setHealth('Ni povezave'))

    // Example API call to fetch a message from the backend
    api.get('/api/pozdrav')
      .then(res => setMessage(res.data.sporocilo || 'No message'))
      .catch(err => setMessage('Error fetching message'))
  }, [])

  return (
    <div className="app" style={{
      // inline fallback using brand colors
      '--primary': brand.primary_color,
      '--secondary': brand.secondary_color,
      '--accent': brand.accent_color,
    }}>
      <header className="header">
        <img src={logoUrl} alt={brand.brand_name} className="logo" />
        <h1>{brand.brand_name}</h1>
      </header>

      <main className="content">
        <section className="card">
          <h2>Dobrodošli v Omni Dashboard</h2>
          <p>Projekt je pripravljen na povezavo z backend API-ji.</p>
          <ul>
            <li>Cloud Run / omni API</li>
            <li>React + Vite</li>
            <li>Branding iz brand_config.json</li>
          </ul>
        </section>

        <section className="card">
          <h3>Status povezave</h3>
          <p><strong>{health || 'Preverjam...'}</strong></p>
        </section>

        <section className="card">
          <h3>API Message</h3>
          <p><strong>{message || 'Loading...'}</strong></p>
        </section>
      </main>

      <footer className="footer">
        <small>&copy; {new Date().getFullYear()} {brand.seo?.site_name || brand.brand_name}</small>
      </footer>
    </div>
  )
}