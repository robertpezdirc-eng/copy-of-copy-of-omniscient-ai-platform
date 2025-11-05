import type { VercelRequest, VercelResponse } from '@vercel/node'

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Placeholder endpoint; replace with Stripe/PayPal integration
  if (req.method === 'GET') {
    return res.status(200).json({ status: 'ok', message: 'Payments API placeholder' })
  }
  return res.status(405).json({ error: 'Method Not Allowed' })
}