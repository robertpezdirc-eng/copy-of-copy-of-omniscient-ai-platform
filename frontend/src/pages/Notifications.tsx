import React, { useEffect, useMemo, useState } from 'react'
import { supabase } from '../lib/supabase'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const Notifications: React.FC = () => {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState('')
  const [severity, setSeverity] = useState('info')

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const { data, error } = await supabase.from('notifications_items').select('*').order('id', { ascending: true })
        if (error) throw error
        if (mounted) setItems(data || [])
      } catch (e: any) { if (mounted) setError(e.message) } finally { if (mounted) setLoading(false) }
    }
    load(); return () => { mounted = false }
  }, [])

  const addItem = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const { error } = await supabase.from('notifications_items').insert([{ message, severity }])
      if (error) throw error
      const { data } = await supabase.from('notifications_items').select('*').order('id', { ascending: true })
      setItems(data || [])
      setMessage(''); setSeverity('info'); setError(null)
    } catch (e: any) { setError(e.message) }
  }

  const chartData = useMemo(() => {
    const counts: Record<string, number> = { info: 0, warning: 0, error: 0 }
    for (const it of items) {
      const sev = String(it.severity || 'info')
      counts[sev] = (counts[sev] || 0) + 1
    }
    return Object.entries(counts).map(([name, count]) => ({ name, count }))
  }, [items])

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Notifications</h1>
      <p>Dodaj obvestila in jih pregleduj.</p>
      <form onSubmit={addItem} style={{ display: 'flex', gap: 12, marginBottom: '1rem' }}>
        <input placeholder="Sporočilo" value={message} onChange={(e) => setMessage(e.target.value)} />
        <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="info">info</option>
          <option value="warning">warning</option>
          <option value="error">error</option>
        </select>
        <button type="submit">Dodaj obvestilo</button>
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
                <Bar dataKey="count" fill="#ff9900" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <ul>
            {items.map((it) => (
              <li key={it.id}>[{it.severity}] {it.message}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

export default Notifications