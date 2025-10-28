import { useState } from 'react'
import { api } from '../api/client'

function isHexColor(v) {
  return /^#?[0-9A-Fa-f]{6}$/.test(v)
}

export default function WhiteLabelSignup() {
  const [tenant, setTenant] = useState('')
  const [brandName, setBrandName] = useState('MyBrand')
  const [primary, setPrimary] = useState('#3b82f6')
  const [secondary, setSecondary] = useState('#111827')
  const [accent, setAccent] = useState('#10b981')
  const [chatEnabled, setChatEnabled] = useState(true)
  const [analyticsEnabled, setAnalyticsEnabled] = useState(true)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const validColors = isHexColor(primary) && isHexColor(secondary) && isHexColor(accent)

  async function submit() {
    setError(''); setResult(null)
    if (!tenant) return setError('Tenant ID je obvezen.')
    if (!validColors) return setError('Barve morajo biti 6‑mestni HEX (npr. #3b82f6).')
    setLoading(true)
    const payload = {
      tenant_id: tenant,
      branding: {
        brand_name: brandName,
        primary_color: primary.startsWith('#') ? primary : `#${primary}`,
        secondary_color: secondary.startsWith('#') ? secondary : `#${secondary}`,
        accent_color: accent.startsWith('#') ? accent : `#${accent}`,
      },
      features: {
        chat_enabled: !!chatEnabled,
        analytics_enabled: !!analyticsEnabled,
      },
      meta: { signup_form: 'react' },
    }
    const res = await api.post('/api/v1/white_label/instances', payload)
    setLoading(false)
    if (!res.ok) {
      setError(`Napaka: ${res.status} ${res.error || ''}`)
    } else {
      setResult(res.data)
    }
  }

  return (
    <div>
      <div style={{display: 'grid', gap: 8}}>
        <input value={tenant} onChange={e => setTenant(e.target.value)} placeholder="Tenant ID" />
        <input value={brandName} onChange={e => setBrandName(e.target.value)} placeholder="Brand name" />
        <div style={{display: 'flex', gap: 8}}>
          <input value={primary} onChange={e => setPrimary(e.target.value)} placeholder="#RRGGBB primary" />
          <input value={secondary} onChange={e => setSecondary(e.target.value)} placeholder="#RRGGBB secondary" />
          <input value={accent} onChange={e => setAccent(e.target.value)} placeholder="#RRGGBB accent" />
        </div>
        <label style={{display: 'flex', gap: 8, alignItems: 'center'}}>
          <input type="checkbox" checked={chatEnabled} onChange={e => setChatEnabled(e.target.checked)} />
          Chat enabled
        </label>
        <label style={{display: 'flex', gap: 8, alignItems: 'center'}}>
          <input type="checkbox" checked={analyticsEnabled} onChange={e => setAnalyticsEnabled(e.target.checked)} />
          Analytics enabled
        </label>
        <button className="btn-primary" onClick={submit} disabled={loading || !tenant || !validColors}>
          {loading ? 'Shranjujem...' : 'Ustvari white‑label instanco'}
        </button>
      </div>
      {error && <p style={{color: 'red', marginTop: 8}}>{error}</p>}
      {result && (
        <div className="card" style={{marginTop: 12}}>
          <h4>White‑label ustvarjen</h4>
          <pre style={{whiteSpace: 'pre-wrap'}}>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}