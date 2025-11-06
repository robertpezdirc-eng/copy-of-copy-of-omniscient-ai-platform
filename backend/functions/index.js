let kvClient = null
const ensureKV = async () => {
  if (kvClient !== null) return
  try {
    const mod = await import('@vercel/kv')
    kvClient = mod.kv
  } catch {
    kvClient = null
  }
}

const mem = {}

const send = (res, status, obj) => {
  res.statusCode = status
  res.setHeader('Content-Type', 'application/json')
  res.end(JSON.stringify(obj))
}

const getKV = async (key) => {
  if (kvClient) {
    try {
      return await kvClient.get(key)
    } catch {
      // Fallback to in-memory store if KV is misconfigured/unavailable
    }
  }
  return mem[key]
}

const setKV = async (key, value) => {
  if (kvClient) {
    try {
      await kvClient.set(key, value)
      return true
    } catch {
      // Fallback to in-memory store if KV is misconfigured/unavailable
    }
  }
  mem[key] = value
  return true
}

export default async function handler(req, res) {
  await ensureKV()
  const origin = req.headers.origin || '*'
  res.setHeader('Access-Control-Allow-Origin', origin)
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')

  if (req.method === 'OPTIONS') {
    res.statusCode = 204
    res.end()
    return
  }

  const url = req.url || '/'
  const method = req.method || 'GET'

  const readBody = () => new Promise((resolve) => {
    let data = ''
    req.on('data', (chunk) => { data += chunk })
    req.on('end', () => {
      try { resolve(JSON.parse(data || '{}')) } catch { resolve({}) }
    })
  })

  // Health
  if (url.startsWith('/api/health')) {
    send(res, 200, { status: 'ok', timestamp: new Date().toISOString() })
    return
  }

  // Finance data (user-provided via KV)
  if (url.startsWith('/api/finance/data')) {
    const data = (await getKV('metrics:finance')) || []
    send(res, 200, { data })
    return
  }

  // Analytics data (user-provided via KV)
  if (url.startsWith('/api/analytics/data')) {
    const data = (await getKV('metrics:analytics')) || []
    send(res, 200, { data })
    return
  }

  // Generic module data endpoints: sales/marketing/operations
  if (url.startsWith('/api/sales/data')) {
    const data = (await getKV('metrics:sales')) || []
    send(res, 200, { data })
    return
  }
  if (url.startsWith('/api/marketing/data')) {
    const data = (await getKV('metrics:marketing')) || []
    send(res, 200, { data })
    return
  }
  if (url.startsWith('/api/operations/data')) {
    const data = (await getKV('metrics:operations')) || []
    send(res, 200, { data })
    return
  }

  // Projects list and status toggle (persisted via KV)
  if (url.startsWith('/api/projects/list')) {
    const projects = (await getKV('projects:list')) || []
    send(res, 200, { projects })
    return
  }
  if (url.startsWith('/api/projects/add') && (method === 'POST')) {
    const body = await readBody()
    const { name } = body
    if (!name || typeof name !== 'string') {
      send(res, 400, { error: 'Invalid name' })
      return
    }
    const current = (await getKV('projects:list')) || []
    const next = [...current, { id: Date.now(), name, status: 'Planning' }]
    await setKV('projects:list', next)
    send(res, 200, { ok: true, projects: next })
    return
  }
  if (url.startsWith('/api/projects/toggle') && (method === 'POST' || method === 'PUT')) {
    const body = await readBody()
    const { id, status } = body
    if (typeof id !== 'number' || !status) {
      send(res, 400, { error: 'Invalid payload' })
      return
    }
    const current = (await getKV('projects:list')) || []
    const next = current.map((it) => it.id === id ? { ...it, status } : it)
    await setKV('projects:list', next)
    send(res, 200, { ok: true, id, status, projects: next })
    return
  }

  // Dashboard layout
  if (url.startsWith('/api/layout')) {
    if (method === 'GET') {
      const layout = (await getKV('dashboard:layout')) || { categories: [] }
      send(res, 200, layout)
      return
    }
    if (method === 'PUT' || method === 'POST') {
      const body = await readBody()
      await setKV('dashboard:layout', body)
      send(res, 200, { ok: true, saved: body })
      return
    }
  }

  // Metrics upsert
  if (url.startsWith('/api/metrics/upsert') && (method === 'POST' || method === 'PUT')) {
    const body = await readBody()
    const { module, entry } = body
    if (!module || typeof module !== 'string' || !entry || typeof entry !== 'object') {
      send(res, 400, { error: 'Invalid payload' })
      return
    }
    const key = `metrics:${module}`
    const current = (await getKV(key)) || []
    const next = [...current, entry]
    await setKV(key, next)
    send(res, 200, { ok: true, module, data: next })
    return
  }

  send(res, 404, { error: 'Not found', path: url })
}