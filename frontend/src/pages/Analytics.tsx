import React, { useEffect, useMemo, useState } from 'react'
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { supabase } from '@/lib/supabase'

const Analytics: React.FC = () => {
  const [threshold, setThreshold] = useState<number>(0)
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [segment, setSegment] = useState('A')
  const [value, setValue] = useState<number>(0)

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const { data: rows, error: err } = await supabase
          .from('analytics_segments')
          .select('*')
          .order('segment', { ascending: true })
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
        .from('analytics_segments')
        .insert([{ segment, value: Number(value) }])
      if (err) throw err
      const { data: rows } = await supabase
        .from('analytics_segments')
        .select('*')
        .order('segment', { ascending: true })
      setData(rows || [])
      setError(null)
    } catch (err: any) {
      setError(err?.message || 'Napaka pri shranjevanju podatkov')
    }
  }

  const filtered = useMemo(() => data.filter(d => d.value >= threshold), [data, threshold])

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Analytics Dashboard</h1>
      <p>Filtriraj segmente po pragu vrednosti za hiter vpogled v KPI-je.</p>
      <div style={{ marginBottom: '1rem' }}>
        <label>
          Threshold: 
          <input type="number" value={threshold} onChange={(e) => setThreshold(Number(e.target.value || 0))} style={{ width: 80 }} />
        </label>
      </div>
      <form onSubmit={addEntry} style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: '1rem' }}>
        <label>
          Segment:
          <input value={segment} onChange={(e) => setSegment(e.target.value)} style={{ marginLeft: 6 }} />
        </label>
        <label>
          Vrednost:
          <input type="number" value={value} onChange={(e) => setValue(Number(e.target.value || 0))} style={{ marginLeft: 6, width: 120 }} />
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
            <BarChart data={filtered}>
              <CartesianGrid stroke="#ccc" />
              <XAxis dataKey="segment" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#5168ff" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

export default Analytics