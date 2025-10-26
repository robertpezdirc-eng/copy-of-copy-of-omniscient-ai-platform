import { useEffect, useMemo, useState } from 'react'

const backendBase = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_URL || ''

function labeledInput(label, value, setValue, placeholder = '') {
  return (
    <label style={{display:'flex', gap:8, alignItems:'center'}}>
      <span style={{width:140}}>{label}</span>
      <input value={value} onChange={e=>setValue(e.target.value)} placeholder={placeholder}
             style={{flex:1, padding:'8px 10px'}} />
    </label>
  )
}

export default function AdminDashboard() {
  const [apiKey, setApiKey] = useState(localStorage.getItem('x_api_key') || '')
  const [tenantId, setTenantId] = useState(localStorage.getItem('tenant_id') || '')
  const [history, setHistory] = useState([])
  const [catalog, setCatalog] = useState([])
  const [addForm, setAddForm] = useState({ name:'', price:'', currency:'USD', scope:'global' })
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')

  useEffect(() => {
    if (apiKey) localStorage.setItem('x_api_key', apiKey)
    if (tenantId) localStorage.setItem('tenant_id', tenantId)
  }, [apiKey, tenantId])

  const commonHeaders = useMemo(() => ({
    'Content-Type': 'application/json',
    'x-api-key': apiKey || '',
    'tenant_id': tenantId || ''
  }), [apiKey, tenantId])

  const loadAll = async () => {
    setErr(''); setMsg('')
    try {
      const hRes = await fetch(`${backendBase}/api/v1/policy/revenue/history`, { headers: commonHeaders })
      const hJson = await hRes.json()
      setHistory(hJson?.history || [])
    } catch (e) { setErr(prev => (prev ? prev+'\n' : '') + `History fetch error: ${e.message}`) }

    try {
      const cRes = await fetch(`${backendBase}/api/v1/billing/catalog`, { headers: commonHeaders })
      const cJson = await cRes.json()
      setCatalog(Array.isArray(cJson?.catalog) ? cJson.catalog : cJson)
    } catch (e) { setErr(prev => (prev ? prev+'\n' : '') + `Catalog fetch error: ${e.message}`) }
  }

  useEffect(() => { if (apiKey && tenantId) loadAll() }, [apiKey, tenantId])

  const generateFromMarket = async () => {
    setErr(''); setMsg('')
    try {
      const trends = [
        { name: 'AI Agents-as-a-Service', sentiment: 'bullish' },
        { name: 'RL-driven FinOps', sentiment: 'neutral' },
        { name: 'Autonomous Cloud Governance', sentiment: 'bullish' }
      ]
      const res = await fetch(`${backendBase}/api/v1/rl/market/process`, {
        method: 'POST', headers: commonHeaders, body: JSON.stringify({ trends })
      })
      const j = await res.json()
      setMsg(`Generated ${j?.created?.length || 0} services and recorded distribution.`)
      await loadAll()
    } catch (e) { setErr(`Market process error: ${e.message}`) }
  }

  const addCatalogItem = async () => {
    setErr(''); setMsg('')
    try {
      const body = { ...addForm, price: Number(addForm.price || 0) }
      const res = await fetch(`${backendBase}/api/v1/billing/catalog/add`, {
        method: 'POST', headers: commonHeaders, body: JSON.stringify(body)
      })
      const j = await res.json()
      setMsg(`Added item: ${j?.id || j?.item?.id || 'ok'}`)
      setAddForm({ name:'', price:'', currency:'USD', scope:'global' })
      await loadAll()
    } catch (e) { setErr(`Add item error: ${e.message}`) }
  }

  const updateCatalogItem = async (id, patch) => {
    setErr(''); setMsg('')
    try {
      const res = await fetch(`${backendBase}/api/v1/billing/catalog/${id}`, {
        method: 'PUT', headers: commonHeaders, body: JSON.stringify(patch)
      })
      const j = await res.json()
      setMsg(`Updated item ${id}`)
      await loadAll()
    } catch (e) { setErr(`Update item error: ${e.message}`) }
  }

  const deleteCatalogItem = async (id) => {
    setErr(''); setMsg('')
    try {
      await fetch(`${backendBase}/api/v1/billing/catalog/${id}`, {
        method: 'DELETE', headers: commonHeaders
      })
      setMsg(`Deleted item ${id}`)
      await loadAll()
    } catch (e) { setErr(`Delete item error: ${e.message}`) }
  }

  return (
    <div className="admin-dashboard" style={{display:'grid', gap:16}}>
      <section className="card">
        <h3>Nastavitve dostopa</h3>
        <div style={{display:'grid', gap:8}}>
          {labeledInput('API Key (x-api-key)', apiKey, setApiKey, 'npr. demo-api-key')}
          {labeledInput('Tenant ID', tenantId, setTenantId, 'npr. finops-demo')}
          <div style={{display:'flex', gap:8}}>
            <button onClick={loadAll}>Osveži podatke</button>
            <button onClick={generateFromMarket}>Generate from Market Data</button>
          </div>
          {msg && <p style={{color:'green'}}>{msg}</p>}
          {err && <p style={{color:'red'}}>{err}</p>}
        </div>
      </section>

      <section className="card">
        <h3>Dodaj katalog item</h3>
        <div style={{display:'grid', gap:8}}>
          {labeledInput('Name', addForm.name, v=>setAddForm(p=>({...p, name:v})), 'Service name')}
          {labeledInput('Price', addForm.price, v=>setAddForm(p=>({...p, price:v})), 'e.g. 99')}
          {labeledInput('Currency', addForm.currency, v=>setAddForm(p=>({...p, currency:v})), 'USD/EUR')}
          {labeledInput('Scope', addForm.scope, v=>setAddForm(p=>({...p, scope:v})), 'global/tenant')}
          <button onClick={addCatalogItem}>Add Catalog Item</button>
        </div>
      </section>

      <section className="card">
        <h3>Revenue History</h3>
        <div style={{display:'grid', gap:8}}>
          {history && history.length ? (
            <ul style={{margin:0, padding:'0 0 0 16px'}}>
              {history.map((h, idx) => (
                <li key={idx}>
                  <strong>{h?.timestamp || h?.ts || idx}</strong> — {h?.note || h?.distribution || h?.action || 'entry'}
                </li>
              ))}
            </ul>
          ) : (
            <p>No history yet. Click "Generate from Market Data".</p>
          )}
        </div>
      </section>

      <section className="card" style={{overflowX:'auto'}}>
        <h3>Billing Catalog</h3>
        <table style={{width:'100%', borderCollapse:'collapse'}}>
          <thead>
            <tr>
              <th style={{textAlign:'left'}}>ID</th>
              <th style={{textAlign:'left'}}>Name</th>
              <th style={{textAlign:'left'}}>Price</th>
              <th style={{textAlign:'left'}}>Currency</th>
              <th style={{textAlign:'left'}}>Scope</th>
              <th style={{textAlign:'left'}}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {catalog && catalog.length ? catalog.map((c) => (
              <tr key={c.id}>
                <td>{c.id}</td>
                <td>{c.name}</td>
                <td>{c.price}</td>
                <td>{c.currency}</td>
                <td>{c.scope || 'global'}</td>
                <td style={{display:'flex', gap:8}}>
                  <button onClick={()=>updateCatalogItem(c.id, { price: Number(c.price||0)+1 })}>+1 price</button>
                  <button onClick={()=>deleteCatalogItem(c.id)}>Delete</button>
                </td>
              </tr>
            )) : (
              <tr><td colSpan={6}>Catalog is empty. Add an item or generate.</td></tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}