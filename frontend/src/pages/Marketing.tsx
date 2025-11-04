import React, { useEffect, useState } from 'react'
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { supabase } from '../lib/supabase'

const Marketing: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [channel, setChannel] = useState('ads')
  const [spend, setSpend] = useState<number>(0)

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const { data: rows, error: err } = await supabase
          .from('marketing_metrics')
          .select('*')
          .order('channel', { ascending: true })
        if (err) throw err
        if (mounted) { setData(rows || []); setError(null) }
      } catch (e: any) {
        if (mounted) setError(e?.message || 'Napaka pri pridobivanju marketinških podatkov')
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load()
    return () => { mounted = false }
  }, [])

  const addEntry = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const { error: err } = await supabase
        .from('marketing_metrics')
        .insert([{ channel, spend: Number(spend) }])
      if (err) throw err
      const { data: rows } = await supabase
        .from('marketing_metrics')
        .select('*')
        .order('channel', { ascending: true })
      setData(rows || [])
      setError(null)
    } catch (err: any) {
      setError(err?.message || 'Napaka pri shranjevanju podatkov')
    }
  }

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Marketing Dashboard</h1>
      <p>Dodaj porabo po kanalu in spremljaj rezultate.</p>
      <form onSubmit={addEntry} style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: '1rem' }}>
        <label>
          Kanal:
          <input type="text" value={channel} onChange={(e) => setChannel(e.target.value)} style={{ marginLeft: 6 }} />
        </label>
        <label>
          Poraba:
          <input type="number" value={spend} onChange={(e) => setSpend(Number(e.target.value || 0))} style={{ marginLeft: 6, width: 120 }} />
        </label>
        <button type="submit">Dodaj porabo</button>
      </form>
      <div style={{ height: 320 }}>
        {loading ? (
          <p>Nalaganje podatkov…</p>
        ) : error ? (
          <p style={{ color: 'red' }}>{error}</p>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid stroke="#ccc" />
              <XAxis dataKey="channel" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="spend" fill="#4dabf7" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

export default Marketing