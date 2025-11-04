import React, { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'

const Assistant: React.FC = () => {
  const [notes, setNotes] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [note, setNote] = useState('')

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const { data, error } = await supabase.from('assistant_notes').select('*').order('id', { ascending: true })
        if (error) throw error
        if (mounted) setNotes(data || [])
      } catch (e: any) { if (mounted) setError(e.message) } finally { if (mounted) setLoading(false) }
    }
    load(); return () => { mounted = false }
  }, [])

  const addNote = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const { error } = await supabase.from('assistant_notes').insert([{ note }])
      if (error) throw error
      const { data } = await supabase.from('assistant_notes').select('*').order('id', { ascending: true })
      setNotes(data || [])
      setNote(''); setError(null)
    } catch (e: any) { setError(e.message) }
  }

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Assistant</h1>
      <p>Dodaj zapiske za pomočnika in jih pregleduj.</p>
      <form onSubmit={addNote} style={{ display: 'flex', gap: 12, marginBottom: '1rem' }}>
        <input placeholder="Zapis" value={note} onChange={(e) => setNote(e.target.value)} />
        <button type="submit">Dodaj zapis</button>
      </form>
      {loading ? <p>Nalaganje…</p> : error ? <p style={{ color: 'red' }}>{error}</p> : (
        <ul>
          {notes.map((n) => (
            <li key={n.id}>{n.note}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default Assistant