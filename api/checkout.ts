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
    const body = (req.body as any) || {}
    const originProto = (req.headers['x-forwarded-proto'] as string) || 'https'
    const host = (req.headers['x-forwarded-host'] as string) || req.headers['host'] || ''
    const origin = host ? `${originProto}://${host}` : (body.origin || 'http://localhost:3000')

    const success_url = body.success_url || `${origin}/checkout/success`
    const cancel_url = body.cancel_url || `${origin}/checkout/cancel`
    const mode = body.mode || 'payment'

    let session
    if (body.priceId) {
      session = await stripe.checkout.sessions.create({
        mode,
        success_url,
        cancel_url,
        line_items: [{ price: body.priceId, quantity: body.quantity || 1 }]
      })
    } else if (Array.isArray(body.line_items)) {
      session = await stripe.checkout.sessions.create({
        mode,
        success_url,
        cancel_url,
        line_items: body.line_items
      })
    } else if (body.amount && body.currency) {
      session = await stripe.checkout.sessions.create({
        mode,
        success_url,
        cancel_url,
        line_items: [{
          price_data: {
            currency: body.currency,
            product_data: { name: body.name || 'Payment' },
            unit_amount: Number(body.amount)
          },
          quantity: 1
        }]
      })
    } else {
      return res.status(400).json({ error: 'Provide priceId, line_items, or amount+currency' })
    }
    return res.status(200).json({ id: session.id, url: session.url, status: session.status })
  } catch (err) {
    return res.status(500).json({ error: (err as Error).message || String(err) })
  }
}