import type { VercelRequest, VercelResponse } from '@vercel/node'

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' })
  }
  const { message } = req.body || {}
  if (!message) {
    return res.status(400).json({ error: 'Missing message' })
  }
  // Placeholder echo response; integrate with actual chat service if needed
  return res.status(200).json({ reply: `Echo: ${message}`, provider: 'vercel-api' })
}