import type { VercelRequest, VercelResponse } from '@vercel/node'

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' })
  }
  try {
    const { message, model } = (req.body as any) || {}
    if (!message) {
      return res.status(400).json({ error: 'Missing message' })
    }

    const chosenModel = model || process.env.OPENAI_MODEL || 'gpt-4o-mini'

    // 1) Try Gateway first if configured
    const gatewayUrl = process.env.GATEWAY_URL
    const gatewayToken = process.env.GATEWAY_TOKEN || process.env.API_KEY
    if (gatewayUrl) {
      try {
        const headers: Record<string, string> = { 'Content-Type': 'application/json' }
        if (gatewayToken) headers['Authorization'] = `Bearer ${gatewayToken}`
        // Some gateways expect X-API-Key instead of Bearer
        if (!headers['Authorization'] && process.env.API_KEY) headers['X-API-Key'] = process.env.API_KEY
        const gwResp = await fetch(`${gatewayUrl.replace(/\/$/, '')}/v1/chat/completions`, {
          method: 'POST',
          headers,
          body: JSON.stringify({
            model: chosenModel,
            messages: [
              { role: 'system', content: 'You are Omni Enterprise assistant.' },
              { role: 'user', content: message }
            ]
          })
        })
        if (gwResp.ok) {
          const gwData = await gwResp.json()
          const reply = gwData?.choices?.[0]?.message?.content ?? gwData?.reply ?? ''
          return res.status(200).json({ reply, model: chosenModel, provider: 'gateway' })
        }
      } catch (_) {
        // Ignore and fall through to OpenAI
      }
    }

    // 2) Fallback to OpenAI if configured
    const apiKey = process.env.OPENAI_API_KEY
    if (!apiKey) {
      return res.status(500).json({ error: 'No provider configured. Set GATEWAY_URL or OPENAI_API_KEY.' })
    }
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: chosenModel,
        messages: [
          { role: 'system', content: 'You are Omni Enterprise assistant.' },
          { role: 'user', content: message }
        ]
      })
    })
    if (!response.ok) {
      const errText = await response.text()
      return res.status(502).json({ error: 'OpenAI API error', details: errText })
    }
    const data = await response.json()
    const reply = data?.choices?.[0]?.message?.content ?? ''
    return res.status(200).json({ reply, model: chosenModel, provider: 'openai' })
  } catch (err) {
    return res.status(500).json({ error: (err as Error).message || String(err) })
  }
}