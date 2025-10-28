import { useEffect, useState } from 'react'
import { api } from '../api/client'
import ReCAPTCHA from 'react-google-recaptcha'

const plans = [
  { id: 'starter', name: 'Starter', price: '$29/mo' },
  { id: 'pro', name: 'Pro', price: '$99/mo' },
  { id: 'enterprise', name: 'Enterprise', price: '$499/mo' },
]

export default function Checkout() {
  const [email, setEmail] = useState('')
  const [plan, setPlan] = useState('starter')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [confirmResult, setConfirmResult] = useState(null)
  const [captchaToken, setCaptchaToken] = useState('')

  const siteKey = import.meta.env.VITE_RECAPTCHA_SITE_KEY || ''

  async function submit() {
    setError(''); setResult(null); setConfirmResult(null); setLoading(true)
    const body = { email, plan }
    if (siteKey) body.recaptchaToken = captchaToken
    const res = await api.post('/api/v1/billing/saas/checkout/mock', body)
    setLoading(false)
    if (!res.ok) {
      setError(`Napaka: ${res.status} ${res.error || ''}`)
    } else {
      setResult(res.data)
    }
  }

  async function confirm() {
    if (!result?.checkout?.session_id) return
    return confirmBySession(result.checkout.session_id)
  }

  async function confirmBySession(sessionId) {
    setError(''); setConfirmResult(null); setConfirming(true)
    const body = { session_id: sessionId }
    if (siteKey) body.recaptchaToken = captchaToken
    const res = await api.post('/api/v1/billing/saas/checkout/confirm', body)
    setConfirming(false)
    if (!res.ok) {
      setError(`Napaka: ${res.status} ${res.error || ''}`)
    } else {
      setConfirmResult(res.data)
    }
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const sid = params.get('session_id')
    if (sid) {
      // Samodejna potrditev po "redirect" simulaciji
      confirmBySession(sid)
    }
  }, [])

  return (
    <div>
      <div style={{display: 'flex', gap: 12, marginBottom: 12}}>
        {plans.map(p => (
          <button key={p.id}
            className={plan === p.id ? 'btn-primary' : 'btn'}
            onClick={() => setPlan(p.id)}>
            {p.name} <small style={{opacity: 0.7}}>({p.price})</small>
          </button>
        ))}
      </div>

      <div style={{display: 'flex', gap: 8}}>
        <input type="email" value={email} onChange={e => setEmail(e.target.value)}
               placeholder="Vaš e‑mail" style={{flex: 1}} />
        <button className="btn-primary" onClick={submit} disabled={loading || !email || (siteKey && !captchaToken)}>
          {loading ? 'Pošiljam...' : 'Mock Checkout'}
        </button>
      </div>

      {siteKey && (
        <div style={{marginTop: 8}}>
          <ReCAPTCHA sitekey={siteKey} onChange={setCaptchaToken} />
        </div>
      )}

      {error && <p style={{color: 'red', marginTop: 8}}>{error}</p>}

      {result && (
        <div className="card" style={{marginTop: 12}}>
          <h4>Uspešno!</h4>
          <pre style={{whiteSpace: 'pre-wrap'}}>{JSON.stringify(result.checkout, null, 2)}</pre>
          <small>Poslana je bila dobrodošlica na {email}.</small>
          <div style={{marginTop: 8}}>
            <button className="btn" onClick={confirm} disabled={confirming || (siteKey && !captchaToken)}>
              {confirming ? 'Potrjujem...' : 'Potrdi sejo'}
            </button>
          </div>
          {confirmResult && (
            <div className="card" style={{marginTop: 8}}>
              <pre style={{whiteSpace: 'pre-wrap'}}>{JSON.stringify(confirmResult, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}