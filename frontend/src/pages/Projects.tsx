import React, { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'

const Projects: React.FC = () => {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newName, setNewName] = useState('')

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const { data, error } = await supabase
          .from('projects_items')
          .select('*')
          .order('id', { ascending: true })
        if (error) throw error
        if (mounted) { setItems(data || []); setError(null) }
      } catch (e: any) {
        if (mounted) setError(e?.message || 'Napaka pri pridobivanju projektov')
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load(); return () => { mounted = false }
  }, [])

  const toggleStatus = async (id: number) => {
    const current = items.find((it) => it.id === id)
    if (!current) return
    const nextStatus = current.status === 'Done' ? 'In Progress' : 'Done'
    setItems(items.map(it => it.id === id ? { ...it, status: nextStatus } : it))
    try {
      const { error } = await supabase
        .from('projects_items')
        .update({ status: nextStatus })
        .eq('id', id)
      if (error) throw error
    } catch {
      setItems(items.map(it => it.id === id ? { ...it, status: current.status } : it))
    }
  }

  const addProject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return
    try {
      const { error } = await supabase
        .from('projects_items')
        .insert([{ name: newName.trim(), status: 'In Progress' }])
      if (error) throw error
      const { data } = await supabase
        .from('projects_items')
        .select('*')
        .order('id', { ascending: true })
      setItems(data || [])
      setNewName('')
      setError(null)
    } catch (err: any) {
      setError(err?.message || 'Napaka pri dodajanju projekta')
    }
  }

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Projects Dashboard</h1>
      <p>Hitri pregled projektov z možnostjo spremembe statusa.</p>
      <form onSubmit={addProject} style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: '1rem' }}>
        <label>
          Ime projekta:
          <input value={newName} onChange={(e) => setNewName(e.target.value)} style={{ marginLeft: 6 }} />
        </label>
        <button type="submit">Dodaj projekt</button>
      </form>
      {loading ? <p>Nalaganje projektov…</p> : error ? <p style={{ color: 'red' }}>{error}</p> : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {items.map(it => (
            <li key={it.id} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              border: '1px solid #ccc', borderRadius: 8, padding: '0.75rem 1rem', marginBottom: '0.5rem'
            }}>
              <span>{it.name}</span>
              <button onClick={() => toggleStatus(it.id)} style={{
                border: '1px solid #999', borderRadius: 6, padding: '0.5rem 0.75rem', background: '#f5f5f5'
              }}>
                {it.status}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default Projects