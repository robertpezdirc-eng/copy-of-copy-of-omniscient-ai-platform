import React, { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'

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
        <ul>
          {items.map((it) => (
            <li key={it.id}>{it.key}: {it.value}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default Settings