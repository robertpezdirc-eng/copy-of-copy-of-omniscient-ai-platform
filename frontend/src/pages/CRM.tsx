import React, { useEffect, useMemo, useState } from 'react'
import { supabase } from '../lib/supabase'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const CRM: React.FC = () => {
  const [contacts, setContacts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const { data, error } = await supabase.from('crm_contacts').select('*').order('id', { ascending: true })
        if (error) throw error
        if (mounted) setContacts(data || [])
      } catch (e: any) { if (mounted) setError(e.message) } finally { if (mounted) setLoading(false) }
    }
    load(); return () => { mounted = false }
  }, [])

  const addContact = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const { error } = await supabase.from('crm_contacts').insert([{ name, email }])
      if (error) throw error
      const { data } = await supabase.from('crm_contacts').select('*').order('id', { ascending: true })
      setContacts(data || [])
      setName(''); setEmail(''); setError(null)
    } catch (e: any) { setError(e.message) }
  }

  const chartData = useMemo(() => {
    const counts: Record<string, number> = {}
    for (const c of contacts) {
      const email = String(c.email || '').toLowerCase()
      const domain = email.includes('@') ? email.split('@')[1] : '(unknown)'
      counts[domain] = (counts[domain] || 0) + 1
    }
    return Object.entries(counts).map(([name, count]) => ({ name, count }))
  }, [contacts])

  return (
    <div style={{ padding: '2rem' }}>
      <h1>CRM</h1>
      <p>Dodaj kontakte in jih pregleduj.</p>
      <form onSubmit={addContact} style={{ display: 'flex', gap: 12, marginBottom: '1rem' }}>
        <input placeholder="Ime" value={name} onChange={(e) => setName(e.target.value)} />
        <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <button type="submit">Dodaj kontakt</button>
      </form>
      {loading ? <p>Nalaganje…</p> : error ? <p style={{ color: 'red' }}>{error}</p> : (
        <>
          <div style={{ height: 220, border: '1px solid #ddd', borderRadius: 8, padding: 12, marginBottom: 16 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#0077ff" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <ul>
            {contacts.map((c) => (
              <li key={c.id}>{c.name} — {c.email}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

export default CRM