import type { VercelRequest, VercelResponse } from '@vercel/node'
import StripeLib from 'stripe'

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' })
  }
  const stripeSecret = process.env.STRIPE_SECRET_KEY
  if (!stripeSecret) {
    return res.status(500).json({ error: 'STRIPE_SECRET_KEY is not configured' })
  }
  const stripe = new StripeLib(stripeSecret, { apiVersion: '2024-09-30' as any })
  try {
    const { amount, currency, payment_method_types } = (req.body as any) || {}
    const validAmount = Number(amount) > 0 ? Number(amount) : 500
    const cur = typeof currency === 'string' ? currency : 'usd'
    const pmTypes = Array.isArray(payment_method_types) ? payment_method_types : ['card']
    const intent = await stripe.paymentIntents.create({
      amount: validAmount,
      currency: cur,
      payment_method_types: pmTypes
    })
    return res.status(200).json({ client_secret: intent.client_secret, id: intent.id, status: intent.status })
  } catch (err) {
    return res.status(500).json({ error: (err as Error).message || String(err) })
  }
}