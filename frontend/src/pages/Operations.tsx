import React, { useEffect, useState } from 'react'
import { AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { supabase } from '../lib/supabase'

const Operations: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [metric, setMetric] = useState('tickets')
  const [value, setValue] = useState<number>(0)

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const { data: rows, error: err } = await supabase
          .from('operations_metrics')
          .select('*')
          .order('metric', { ascending: true })
        if (err) throw err
        if (mounted) { setData(rows || []); setError(null) }
      } catch (e: any) {
        if (mounted) setError(e?.message || 'Napaka pri pridobivanju operativnih podatkov')
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
        .from('operations_metrics')
        .insert([{ metric, value: Number(value) }])
      if (err) throw err
      const { data: rows } = await supabase
        .from('operations_metrics')
        .select('*')
        .order('metric', { ascending: true })
      setData(rows || [])
      setError(null)
    } catch (err: any) {
      setError(err?.message || 'Napaka pri shranjevanju podatkov')
    }
  }

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Operations Dashboard</h1>
      <p>Dodaj operativne metrike (npr. ticketi, SLA, uptime).</p>
      <form onSubmit={addEntry} style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: '1rem' }}>
        <label>
          Metrika:
          <input type="text" value={metric} onChange={(e) => setMetric(e.target.value)} style={{ marginLeft: 6 }} />
        </label>
        <label>
          Vrednost:
          <input type="number" value={value} onChange={(e) => setValue(Number(e.target.value || 0))} style={{ marginLeft: 6, width: 120 }} />
        </label>
        <button type="submit">Dodaj metriko</button>
      </form>
      <div style={{ height: 320 }}>
        {loading ? (
          <p>Nalaganje podatkov…</p>
        ) : error ? (
          <p style={{ color: 'red' }}>{error}</p>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <CartesianGrid stroke="#ccc" />
              <XAxis dataKey="metric" />
              <YAxis />
              <Tooltip />
              <Area type="monotone" dataKey="value" stroke="#38d9a9" fill="#c3fae8" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

export default Operations