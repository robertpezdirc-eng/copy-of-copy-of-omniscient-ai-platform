import type { VercelRequest, VercelResponse } from '@vercel/node'
import StripeLib from 'stripe'

export const config = {
  // Hint to Vercel to avoid body parsing issues (best-effort; Node builder may differ)
  api: { bodyParser: false }
} as any

export default async function handler(req: VercelRequest & { rawBody?: string | Buffer }, res: VercelResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' })
  }
  const stripeSecret = process.env.STRIPE_SECRET_KEY
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET
  if (!stripeSecret) {
    return res.status(500).json({ error: 'STRIPE_SECRET_KEY is not configured' })
  }
  const stripe = new StripeLib(stripeSecret, { apiVersion: '2024-09-30' as any })
  try {
    const sig = req.headers['stripe-signature'] as string | undefined
    let event: StripeLib.Event
    if (webhookSecret && sig) {
      const raw = (req as any).rawBody || (typeof (req as any).body === 'string' ? (req as any).body : JSON.stringify((req as any).body || {}))
      event = stripe.webhooks.constructEvent(raw, sig, webhookSecret)
    } else {
      event = (req as any).body as StripeLib.Event
    }

    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as StripeLib.Checkout.Session
        // TODO: fulfill order, update DB, etc.
        break
      }
      case 'payment_intent.succeeded': {
        // Handle PaymentIntent success
        break
      }
      default:
        break
    }
    return res.status(200).json({ received: true })
  } catch (err) {
    return res.status(400).json({ error: (err as Error).message || String(err) })
  }
}