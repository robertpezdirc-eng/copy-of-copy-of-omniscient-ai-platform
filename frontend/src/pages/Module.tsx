import React, { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const randomSeries = (seed: number) => {
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  let s = seed
  return months.map((m) => { s = (s * 9301 + 49297) % 233280; const v = 10000 + (s % 15000); return { month: m, value: v } })
}

const Module: React.FC = () => {
  const { slug = 'mod' } = useParams()
  const [toggle, setToggle] = useState<boolean>(true)
  const [scale, setScale] = useState<'linear' | 'log'>('linear')
  const data = useMemo(() => randomSeries(slug.length), [slug])

  useEffect(() => { window.scrollTo(0, 0) }, [slug])

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Modul: {slug}</h1>
      <p>Interaktivna predstavitev modula z grafom in nastavitvami.</p>
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
        <label>
          <input type="checkbox" checked={toggle} onChange={() => setToggle(!toggle)} />{' '}
          Omogoči funkcijo
        </label>
        <label>
          Skala:{' '}
          <select value={scale} onChange={(e) => setScale(e.target.value as 'linear' | 'log')}>
            <option value="linear">Linear</option>
            <option value="log">Log</option>
          </select>
        </label>
      </div>
      <div style={{ height: 320 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid stroke="#ddd" />
            <XAxis dataKey="month" />
            <YAxis scale={scale} />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke={toggle ? '#1e90ff' : '#999'} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default Module