import type { VercelRequest, VercelResponse } from '@vercel/node'

export default async function handler(req: VercelRequest, res: VercelResponse) {
  try {
    res.status(200).json({ status: 'ok', platform: 'vercel', timestamp: new Date().toISOString() })
  } catch (err) {
    res.status(500).json({ status: 'error', message: (err as Error).message })
  }
}