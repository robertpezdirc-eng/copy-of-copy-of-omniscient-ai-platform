import React, { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'

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
        <ul>
          {contacts.map((c) => (
            <li key={c.id}>{c.name} — {c.email}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default CRM