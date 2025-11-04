let mem = { }
let kvClient = null
try { kvClient = require('@vercel/kv').kv } catch { kvClient = null }

const getKV = async (key) => {
  if (kvClient) return await kvClient.get(key)
  return mem[key]
}
const setKV = async (key, value) => {
  if (kvClient) return await kvClient.set(key, value)
  mem[key] = value
  return true
}

module.exports = async (req, res) => {
  const origin = req.headers.origin || '*'
  res.setHeader('Access-Control-Allow-Origin', origin)
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')

  if (req.method === 'OPTIONS') {
    res.status(204).end()
    return
  }

  const url = req.url || '/'
  const method = req.method || 'GET'

  // Utility to read JSON body for POST/PUT
  const readBody = () => new Promise((resolve) => {
    let data = ''
    req.on('data', (chunk) => { data += chunk })
    req.on('end', () => {
      try { resolve(JSON.parse(data || '{}')) } catch { resolve({}) }
    })
  })

  // Health
  if (url.startsWith('/api/health')) {
    res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() })
    return
  }

  // Finance data (user-provided via KV)
  if (url.startsWith('/api/finance/data')) {
    const data = (await getKV('metrics:finance')) || []
    res.status(200).json({ data })
    return
  }

  // Analytics data (user-provided via KV)
  if (url.startsWith('/api/analytics/data')) {
    const data = (await getKV('metrics:analytics')) || []
    res.status(200).json({ data })
    return
  }

  // Generic module data endpoints: sales/marketing/operations
  if (url.startsWith('/api/sales/data')) {
    const data = (await getKV('metrics:sales')) || []
    res.status(200).json({ data })
    return
  }
  if (url.startsWith('/api/marketing/data')) {
    const data = (await getKV('metrics:marketing')) || []
    res.status(200).json({ data })
    return
  }
  if (url.startsWith('/api/operations/data')) {
    const data = (await getKV('metrics:operations')) || []
    res.status(200).json({ data })
    return
  }

  // Projects list and status toggle (persisted via KV)
  if (url.startsWith('/api/projects/list')) {
    const projects = (await getKV('projects:list')) || []
    res.status(200).json({ projects })
    return
  }
  if (url.startsWith('/api/projects/add') && (method === 'POST')) {
    const body = await readBody()
    const { name } = body
    if (!name || typeof name !== 'string') {
      res.status(400).json({ error: 'Invalid name' })
      return
    }
    const current = (await getKV('projects:list')) || []
    const next = [...current, { id: Date.now(), name, status: 'Planning' }]
    await setKV('projects:list', next)
    res.status(200).json({ ok: true, projects: next })
    return
  }
  if (url.startsWith('/api/projects/toggle') && (method === 'POST' || method === 'PUT')) {
    const body = await readBody()
    const { id, status } = body
    if (typeof id !== 'number' || !status) {
      res.status(400).json({ error: 'Invalid payload' })
      return
    }
    const current = (await getKV('projects:list')) || []
    const next = current.map((it) => it.id === id ? { ...it, status } : it)
    await setKV('projects:list', next)
    res.status(200).json({ ok: true, id, status, projects: next })
    return
  }

  // Dashboard layout (stateless server; client should persist in localStorage)
  if (url.startsWith('/api/layout')) {
    if (method === 'GET') {
      const layout = (await getKV('dashboard:layout')) || { categories: [] }
      res.status(200).json(layout)
      return
    }
    if (method === 'PUT' || method === 'POST') {
      const body = await readBody()
      await setKV('dashboard:layout', body)
      res.status(200).json({ ok: true, saved: body })
      return
    }
  }

  // Metrics upsert (Finance/Analytics/any module)
  if (url.startsWith('/api/metrics/upsert') && (method === 'POST' || method === 'PUT')) {
    const body = await readBody()
    const { module, entry } = body
    if (!module || typeof module !== 'string' || !entry || typeof entry !== 'object') {
      res.status(400).json({ error: 'Invalid payload' })
      return
    }
    const key = `metrics:${module}`
    const current = (await getKV(key)) || []
    const next = [...current, entry]
    await setKV(key, next)
    res.status(200).json({ ok: true, module, data: next })
    return
  }

  res.status(404).json({ error: 'Not found', path: url })
}