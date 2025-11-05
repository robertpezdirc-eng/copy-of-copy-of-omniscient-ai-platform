import type { VercelRequest, VercelResponse } from '@vercel/node'

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Placeholder summary endpoint
  const summary = {
    uptime: process.uptime(),
    env: process.env.NODE_ENV,
    timestamp: new Date().toISOString()
  }
  return res.status(200).json({ status: 'ok', data: summary })
}