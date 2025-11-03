# Omni Customer Portal

Customer-facing portal for the Omni Enterprise Ultra Max platform.

## Features

- **Dashboard** - Usage overview and quick actions
- **Usage Analytics** - Detailed API usage metrics
- **Billing** - Invoices and payment management
- **Support** - Ticket system
- **API Keys** - Self-service key management
- **Profile** - Account settings
- **Notifications** - Activity feed
- **PWA** - Offline support and push notifications

## Quick Start

```bash
cd customer-portal
npm install
npm run dev
```

## Environment Variables

```env
VITE_API_URL=http://localhost:8080/api/v1
```

## Build

```bash
npm run build
```

## Deploy

```bash
gcloud run deploy omni-customer-portal \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars VITE_API_URL=https://api.omniscient.ai/api/v1
```

## Pages

- **/dashboard** - Overview
- **/usage** - Usage analytics
- **/billing** - Billing & invoices
- **/support** - Support tickets
- **/api-keys** - API key management
- **/profile** - User profile
- **/notifications** - Notifications

## Technology

- React 18 + TypeScript
- Material-UI
- Chart.js
- Vite
- PWA capabilities

## License

Proprietary
