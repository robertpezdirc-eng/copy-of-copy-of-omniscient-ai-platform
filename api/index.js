module.exports = async (req, res) => {
  const url = req.url || '/'
  if (url.startsWith('/api/health')) {
    res.statusCode = 200
    res.setHeader('Content-Type', 'application/json')
    res.end(JSON.stringify({ status: 'ok', timestamp: new Date().toISOString() }))
    return
  }
  try {
    const mod = await import('../backend/index.js')
    const handler = mod && (mod.default || mod)
    if (typeof handler === 'function') {
      return handler(req, res)
    }
    throw new Error('Invalid backend handler')
  } catch (err) {
    res.statusCode = 500
    res.setHeader('Content-Type', 'application/json')
    res.end(JSON.stringify({ error: 'backend_import_failed', message: String(err && err.message || err) }))
  }
}