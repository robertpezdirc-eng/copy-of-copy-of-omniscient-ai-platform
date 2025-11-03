# Omni Enterprise Ultra Max - Web Dashboard

Modern, responsive admin dashboard for managing the Omni Enterprise Ultra Max platform.

## Features

### 🎯 Core Features
- **Dashboard Overview** - Real-time metrics, charts, and activity feed
- **Tenant Management** - Complete CRUD operations for multi-tenant SaaS
- **User Management** - User administration with role-based access control
- **Analytics** - Interactive charts and reports with Recharts
- **Reports** - Generate and schedule automated reports
- **Integrations** - Manage third-party integrations (Slack, Teams, etc.)
- **ML Models** - AI/ML model lifecycle management
- **Security** - 2FA, SSO, audit logs, security scanning
- **Settings** - System configuration and preferences

### 🚀 Technical Features
- **React 18** + TypeScript for type safety
- **Material-UI (MUI)** for beautiful, accessible UI
- **Vite** for lightning-fast builds
- **React Query** for server state management
- **React Router v6** for client-side routing
- **Axios** with interceptors for API calls
- **Dark/Light Theme** support
- **PWA** (Progressive Web App) capabilities
- **Offline** support with service worker
- **Push Notifications** via Web Push API

## Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

```bash
cd web-dashboard
npm install
```

### Development

```bash
npm run dev
```

Opens at `http://localhost:5173`

### Environment Variables

Create `.env` file:

```env
VITE_API_URL=http://localhost:8080/api/v1
VITE_WS_URL=ws://localhost:8080/ws
```

### Build for Production

```bash
npm run build
```

Output directory: `dist/`

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
web-dashboard/
├── public/              # Static assets
│   ├── manifest.json   # PWA manifest
│   ├── service-worker.js  # Service worker
│   └── icons/          # App icons
├── src/
│   ├── main.tsx        # Entry point
│   ├── App.tsx         # Root component
│   ├── components/     # Reusable components
│   │   ├── Layout.tsx
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   └── ...
│   ├── pages/          # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Tenants.tsx
│   │   ├── Users.tsx
│   │   └── ...
│   ├── services/       # API services
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── ...
│   ├── contexts/       # React contexts
│   │   └── AuthContext.tsx
│   ├── hooks/          # Custom hooks
│   │   └── useAuth.ts
│   └── utils/          # Utilities
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## Pages

### Dashboard
Real-time overview with key metrics:
- Active tenants, total users, revenue, API calls
- Revenue chart (last 30 days)
- Usage chart
- Recent activity feed

### Tenants
Manage tenants with:
- List view with search and filters
- Create/edit tenant forms
- Subscription tier management
- Usage statistics
- Suspend/activate actions

### Users
User administration:
- User list with role filters
- Create users with role assignment
- Edit user details
- Password reset
- User suspension

### Analytics
Interactive analytics dashboard:
- Multiple chart types (line, bar, pie, area)
- Time range filters (7d, 30d, 90d, custom)
- Export data (CSV, Excel, PDF)
- Real-time updates

### Reports
Report generation and scheduling:
- Custom report builder
- Report templates
- Schedule automated reports
- Email delivery configuration
- Report history

### Integrations
Third-party integration management:
- Slack integration
- Microsoft Teams integration
- Generic webhooks
- OAuth providers
- Integration logs

### ML Models
AI/ML model management:
- List all models
- Train new models
- Model versioning
- A/B testing
- Deploy/rollback

### Security
Security management:
- 2FA configuration
- SSO setup
- Audit log viewer
- Security scanning results
- Vulnerability management

### Settings
System configuration:
- Email templates
- API keys
- Notifications
- Backups

## API Integration

All API calls go through the centralized API service with:
- Automatic JWT token handling
- Token refresh logic
- Error handling
- Request/response interceptors

Example:

```typescript
import { apiService } from './services/api';

// Get tenants
const tenants = await apiService.get('/tenants');

// Create tenant
const newTenant = await apiService.post('/tenants', {
  name: 'Acme Corp',
  tier: 'pro',
});
```

## Authentication

JWT-based authentication with:
- Login/logout
- Auto token refresh
- Protected routes
- Role-based access

```typescript
import { useAuth } from './hooks/useAuth';

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth();
  
  // Use auth state
}
```

## PWA Features

### Offline Support
- Service worker caches assets
- Offline fallback pages
- Background sync for pending actions

### Push Notifications
- Web Push API integration
- Notification permission handling
- Click actions

### Installable
- Add to Home Screen (Android)
- Install prompt (Desktop)
- Standalone mode

## Deployment

### Cloud Run (Recommended)

```bash
# Build
npm run build

# Deploy
gcloud run deploy omni-dashboard \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars VITE_API_URL=https://api.omniscient.ai/api/v1
```

### Static Hosting

```bash
# Build
npm run build

# Upload to Cloud Storage
gsutil -m cp -r dist/* gs://omni-dashboard/

# Configure CDN
gcloud compute backend-buckets create omni-dashboard-backend \
  --gcs-bucket-name=omni-dashboard
```

## Testing

```bash
# Run tests
npm run test

# Coverage
npm run test:coverage
```

## Linting

```bash
npm run lint
```

## Performance

- First Contentful Paint (FCP): < 1.2s
- Largest Contentful Paint (LCP): < 2.5s
- Time to Interactive (TTI): < 3.5s
- Lighthouse Score: 95+

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Create feature branch
2. Make changes
3. Run tests and linting
4. Submit pull request

## License

Proprietary - Omni Enterprise Ultra Max

## Support

For support, email support@omniscient.ai
