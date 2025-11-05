import React, { useEffect, useState } from 'react'
import { LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { supabase } from '@/lib/supabase'

const Finance: React.FC = () => {
  const [scale, setScale] = useState<'linear' | 'log'>('linear')
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [month, setMonth] = useState('Jan')
  const [revenue, setRevenue] = useState<number>(0)

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const { data: rows, error: err } = await supabase
          .from('finance_metrics')
          .select('*')
          .order('month', { ascending: true })
        if (err) throw err
        if (mounted) { setData(rows || []); setError(null) }
      } catch (e: any) {
        if (mounted) setError(e?.message || 'Napaka pri pridobivanju podatkov')
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
        .from('finance_metrics')
        .insert([{ month, revenue: Number(revenue) }])
      if (err) throw err
      const { data: rows } = await supabase
        .from('finance_metrics')
        .select('*')
        .order('month', { ascending: true })
      setData(rows || [])
      setError(null)
    } catch (err: any) {
      setError(err?.message || 'Napaka pri shranjevanju podatkov')
    }
  }

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Finance Dashboard</h1>
      <p>Pregled prihodkov po mesecih z možnostjo spremembe skale.</p>
      <div style={{ marginBottom: '1rem' }}>
        <label>
          Scale: 
          <select value={scale} onChange={(e) => setScale(e.target.value as 'linear' | 'log')}>
            <option value="linear">Linear</option>
            <option value="log">Log</option>
          </select>
        </label>
      </div>
      <form onSubmit={addEntry} style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: '1rem' }}>
        <label>
          Mesec:
          <input value={month} onChange={(e) => setMonth(e.target.value)} style={{ marginLeft: 6 }} />
        </label>
        <label>
          Prihodek:
          <input type="number" value={revenue} onChange={(e) => setRevenue(Number(e.target.value || 0))} style={{ marginLeft: 6, width: 120 }} />
        </label>
        <button type="submit">Dodaj podatek</button>
      </form>
      <div style={{ height: 320 }}>
        {loading ? (
          <p>Nalaganje podatkov…</p>
        ) : error ? (
          <p style={{ color: 'red' }}>{error}</p>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid stroke="#ccc" />
              <XAxis dataKey="month" />
              <YAxis scale={scale} />
              <Tooltip />
              <Line type="monotone" dataKey="revenue" stroke="#00a97f" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

export default Finance