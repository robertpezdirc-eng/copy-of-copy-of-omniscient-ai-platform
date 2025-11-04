import React, { useEffect, useState } from 'react'
import { api } from '../lib/api'

const Projects: React.FC = () => {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newName, setNewName] = useState('')

  useEffect(() => {
    let mounted = true
    api.get('/projects/list')
      .then((res) => { if (mounted) { setItems(res.data?.projects || []); setError(null) } })
      .catch((e) => { if (mounted) setError(e?.message || 'Napaka pri pridobivanju projektov') })
      .finally(() => { if (mounted) setLoading(false) })
    return () => { mounted = false }
  }, [])

  const toggleStatus = async (id: number) => {
    const current = items.find((it) => it.id === id)
    if (!current) return
    const nextStatus = current.status === 'Done' ? 'In Progress' : 'Done'
    // Optimistic update
    setItems(items.map(it => it.id === id ? { ...it, status: nextStatus } : it))
    try { await api.post('/projects/toggle', { id, status: nextStatus }) } catch {
      // Revert on error
      setItems(items.map(it => it.id === id ? { ...it, status: current.status } : it))
    }
  }

  const addProject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return
    try {
      const res = await api.post('/projects/add', { name: newName.trim() })
      setItems(res.data?.projects || [])
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