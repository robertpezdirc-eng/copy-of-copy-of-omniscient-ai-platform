import React, { useEffect, useMemo, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

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

  const graphData = useMemo(() => {
    const sorted = [...notes].sort((a, b) => Number(a.id) - Number(b.id))
    let cumulative = 0
    return sorted.map((n, idx) => {
      cumulative += 1
      const created = n.created_at ? new Date(n.created_at) : null
      const label = created ? created.toISOString().slice(0,10) : String(idx + 1)
      return { x: label, count: cumulative }
    })
  }, [notes])

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Assistant</h1>
      <p>Dodaj zapiske za pomočnika in jih pregleduj.</p>
      <form onSubmit={addNote} style={{ display: 'flex', gap: 12, marginBottom: '1rem' }}>
        <input placeholder="Zapis" value={note} onChange={(e) => setNote(e.target.value)} />
        <button type="submit">Dodaj zapis</button>
      </form>
      {loading ? <p>Nalaganje…</p> : error ? <p style={{ color: 'red' }}>{error}</p> : (
        <>
          <div style={{ height: 220, border: '1px solid #ddd', borderRadius: 8, padding: 12, marginBottom: 16 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={graphData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="#eee" />
                <XAxis dataKey="x" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#8b5cf6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <ul>
            {notes.map((n) => (
              <li key={n.id}>{n.note}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

export default Assistant