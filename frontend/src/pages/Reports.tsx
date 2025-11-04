import React, { useEffect, useMemo, useState } from 'react'
import { supabase } from '../lib/supabase'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const Reports: React.FC = () => {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [editItem, setEditItem] = useState<any | null>(null)

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const { data, error } = await supabase.from('reports_items').select('*').order('id', { ascending: true })
        if (error) throw error
        if (mounted) setItems(data || [])
      } catch (e: any) { if (mounted) setError(e.message) } finally { if (mounted) setLoading(false) }
    }
    load(); return () => { mounted = false }
  }, [])

  const addItem = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const { error } = await supabase.from('reports_items').insert([{ title, content }])
      if (error) throw error
      const { data } = await supabase.from('reports_items').select('*').order('id', { ascending: true })
      setItems(data || [])
      setTitle(''); setContent(''); setError(null)
    } catch (e: any) { setError(e.message) }
  }

  const chartData = useMemo(() => {
    const counts: Record<string, number> = {}
    for (const it of items) {
      const key = String(it.title || '').trim() || '(untitled)'
      counts[key] = (counts[key] || 0) + 1
    }
    return Object.entries(counts).map(([name, count]) => ({ name, count }))
  }, [items])

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Reports</h1>
      <p>Dodaj poročila in jih pregleduj.</p>
      <form onSubmit={addItem} style={{ display: 'flex', gap: 12, marginBottom: '1rem' }}>
        <input placeholder="Naslov" value={title} onChange={(e) => setTitle(e.target.value)} />
        <input placeholder="Vsebina" value={content} onChange={(e) => setContent(e.target.value)} />
        <button type="submit">Dodaj poročilo</button>
      </form>
      {loading ? <p>Nalaganje…</p> : error ? <p style={{ color: 'red' }}>{error}</p> : (
        <>
          <div style={{ height: 240, border: '1px solid #ddd', borderRadius: 8, padding: 12, marginBottom: 16 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#00c389" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <ul>
            {items.map((it) => (
              <li key={it.id}>
                <strong>{it.title}</strong>: {it.content}
                <button style={{ marginLeft: 8 }} onClick={() => setEditItem({ ...it })}>Uredi</button>
              </li>
            ))}
          </ul>
          {editItem && (
            <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ background: '#fff', padding: '1rem', borderRadius: 8, minWidth: 320 }}>
                <h3>Uredi poročilo</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <input value={editItem.title} onChange={(e) => setEditItem({ ...editItem, title: e.target.value })} />
                  <input value={editItem.content} onChange={(e) => setEditItem({ ...editItem, content: e.target.value })} />
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                  <button onClick={async () => {
                    try {
                      const { error } = await supabase
                        .from('reports_items')
                        .update({ title: editItem.title, content: editItem.content })
                        .eq('id', editItem.id)
                      if (error) throw error
                      const { data } = await supabase.from('reports_items').select('*').order('id', { ascending: true })
                      setItems(data || [])
                      setEditItem(null)
                    } catch (e: any) { setError(e.message) }
                  }}>Shrani</button>
                  <button onClick={() => setEditItem(null)}>Prekliči</button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default Reports