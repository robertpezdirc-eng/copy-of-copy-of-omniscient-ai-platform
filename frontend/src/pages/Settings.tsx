import React, { useEffect, useMemo, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const Settings: React.FC = () => {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [keyName, setKeyName] = useState('')
  const [value, setValue] = useState('')

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const { data, error } = await supabase.from('settings_items').select('*').order('id', { ascending: true })
        if (error) throw error
        if (mounted) setItems(data || [])
      } catch (e: any) { if (mounted) setError(e.message) } finally { if (mounted) setLoading(false) }
    }
    load(); return () => { mounted = false }
  }, [])

  const addItem = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const { error } = await supabase.from('settings_items').insert([{ key: keyName, value }])
      if (error) throw error
      const { data } = await supabase.from('settings_items').select('*').order('id', { ascending: true })
      setItems(data || [])
      setKeyName(''); setValue(''); setError(null)
    } catch (e: any) { setError(e.message) }
  }

  const chartData = useMemo(() => {
    const counts: Record<string, number> = {}
    for (const it of items) {
      const key = String(it.key || '').trim() || '(unknown)'
      counts[key] = (counts[key] || 0) + 1
    }
    return Object.entries(counts).map(([name, count]) => ({ name, count }))
  }, [items])

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Settings</h1>
      <p>Dodaj nastavitve (ključ/vrednost) in jih pregleduj.</p>
      <form onSubmit={addItem} style={{ display: 'flex', gap: 12, marginBottom: '1rem' }}>
        <input placeholder="Ključ" value={keyName} onChange={(e) => setKeyName(e.target.value)} />
        <input placeholder="Vrednost" value={value} onChange={(e) => setValue(e.target.value)} />
        <button type="submit">Shrani nastavitev</button>
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
                <Bar dataKey="count" fill="#22c55e" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <ul>
            {items.map((it) => (
              <li key={it.id}>{it.key}: {it.value}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

export default Settings