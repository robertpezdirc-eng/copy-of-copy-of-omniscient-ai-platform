# Omni Enterprise Ultra Max - Frontend

Modern React + TypeScript frontend for Omni Enterprise Ultra Max platform.

## 🚀 Features

- ⚡ **React 18** with TypeScript
- 🎨 **Modern UI** with gradient designs
- 🔐 **Authentication** with JWT
- 📱 **Responsive** design
- 🎯 **State Management** with Zustand
- 🔄 **API Integration** with Axios
- 🎨 **Toast Notifications**
- 📊 **Real-time Dashboard**

## 📦 Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

## 🛠️ Development

```bash
# Development server (port 3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## 🐳 Docker

```bash
# Build image
docker build -t omni-frontend .

# Run container
docker run -p 80:80 omni-frontend
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable components
│   │   ├── Layout.tsx
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   ├── PrivateRoute.tsx
│   │   └── AdminAlertsPanel.tsx
│   ├── contexts/         # React contexts
│   │   └── AuthContext.tsx
│   ├── pages/            # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Profile.tsx
│   │   ├── Pricing.tsx
│   │   ├── AffiliateDashboard.tsx
│   │   └── AdminPanel.tsx
│   ├── lib/              # Utilities
│   │   └── api.ts
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── public/               # Static assets
├── Dockerfile            # Docker configuration
├── nginx.conf            # Nginx configuration
├── vite.config.ts        # Vite configuration
├── tsconfig.json         # TypeScript configuration
└── package.json          # Dependencies
```

## 🎨 Pages

### Public Pages
- **Login** (`/login`) - User authentication
- **Register** (`/register`) - User registration
- **Pricing** (`/pricing`) - Subscription plans

### Protected Pages (require authentication)
- **Dashboard** (`/dashboard`) - Main dashboard with stats
- **Profile** (`/profile`) - User profile settings
- **Affiliate** (`/affiliate`) - Affiliate dashboard
- **Admin** (`/admin`) - Admin panel with alerts

## 🔧 Environment Variables

```env
VITE_API_URL=http://localhost:8080
VITE_APP_NAME=Omni Enterprise Ultra Max
VITE_APP_VERSION=2.0.0
```

## 🚀 Deployment

### Cloud Run (GCP)

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/omni-frontend

# Deploy to Cloud Run
gcloud run deploy omni-frontend \
  --image gcr.io/PROJECT_ID/omni-frontend \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated
```

## 📝 API Integration

The frontend communicates with the backend API through axios:

- Base URL configured via `VITE_API_URL`
- Automatic JWT token injection
- Request/response interceptors
- Automatic logout on 401 errors

## 🎯 Key Features

### Authentication
- JWT-based authentication
- Persistent sessions (localStorage)
- Protected routes
- Automatic token refresh

### Dashboard
- Real-time statistics
- Activity feed
- Quick actions
- Performance metrics

### Affiliate System
- Commission tracking
- Click analytics
- Tier progression
- Custom tracking links

### Admin Panel
- System overview
- Real-time alerts
- User management
- System settings

## 🔐 Security

- XSS protection
- CSRF protection
- Secure headers (configured in nginx)
- Content Security Policy
- HTTPS-only cookies (production)

## 📊 Performance

- Code splitting
- Lazy loading
- Asset optimization
- Gzip compression
- Browser caching

## 🐛 Troubleshooting

### Development Issues

**Port already in use:**
```bash
# Change port in vite.config.ts or use different port
npm run dev -- --port 3001
```

**API connection refused:**
```bash
# Check backend is running
# Update VITE_API_URL in .env
```

### Production Issues

**Build fails:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

## 📄 License

Copyright © 2025 Omni Enterprise Ultra Max
