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
    const apiKey = process.env.OPENAI_API_KEY
    if (!apiKey) {
      return res.status(500).json({ error: 'OPENAI_API_KEY is not configured' })
    }
    const chosenModel = model || process.env.OPENAI_MODEL || 'gpt-4o-mini'
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