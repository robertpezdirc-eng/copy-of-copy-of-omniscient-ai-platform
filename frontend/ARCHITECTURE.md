# Frontend Architecture

This document describes the architecture and organization of the Omni Enterprise Ultra Max frontend application.

## Technology Stack

- **Framework**: React 18.3+ with TypeScript
- **Build Tool**: Vite 5.4+
- **Routing**: React Router DOM v6
- **State Management**: Zustand + Context API
- **HTTP Client**: Axios
- **Styling**: Custom CSS with CSS Variables
- **Charts**: Recharts (business charts) + D3.js (custom visualizations)
- **Real-time**: Socket.IO Client
- **UI Components**: Lucide React (icons)
- **Notifications**: React Hot Toast

## Project Structure

```
frontend/
├── src/
│   ├── App.tsx                    # Main application component
│   ├── main.tsx                   # Application entry point
│   ├── index.css                  # Global styles and CSS variables
│   ├── vite-env.d.ts             # Vite type definitions
│   │
│   ├── components/                # Reusable components
│   │   ├── Layout.tsx            # Main layout wrapper
│   │   ├── Navbar.tsx            # Top navigation bar
│   │   ├── Sidebar.tsx           # Side navigation menu
│   │   ├── PrivateRoute.tsx      # Route protection HOC
│   │   └── dashboard/            # Dashboard-specific components
│   │       ├── RealTimeMetrics.tsx   # Real-time metrics display
│   │       └── D3Visualizations.tsx  # D3.js custom charts
│   │
│   ├── pages/                     # Page components
│   │   ├── Dashboard.tsx         # Main dashboard
│   │   ├── BIDashboard.tsx       # Business Intelligence dashboard
│   │   ├── Login.tsx             # Login page
│   │   ├── Register.tsx          # Registration page
│   │   ├── Profile.tsx           # User profile
│   │   ├── Pricing.tsx           # Pricing plans
│   │   ├── AffiliateDashboard.tsx # Affiliate management
│   │   ├── AdminPanel.tsx        # Admin controls
│   │   └── Health.tsx            # System health monitoring
│   │
│   ├── contexts/                  # React Context providers
│   │   └── AuthContext.tsx       # Authentication context
│   │
│   ├── hooks/                     # Custom React hooks
│   │   └── useWebSocket.ts       # WebSocket connection hook
│   │
│   └── lib/                       # Utility libraries
│       └── api.ts                # Axios instance and interceptors
│
├── public/                        # Static assets
├── index.html                     # HTML template
├── package.json                   # Dependencies and scripts
├── tsconfig.json                  # TypeScript configuration
├── vite.config.ts                # Vite build configuration
├── nginx.conf                     # Production nginx config
├── Dockerfile                     # Container image definition
└── docker-entrypoint.sh          # Container startup script
```

## Core Components

### 1. Application Root (`App.tsx`)

The main application component that sets up:
- **Router**: Browser-based routing
- **AuthProvider**: Authentication context
- **Toast Notifications**: Global notification system
- **Route Definitions**: Public and protected routes

**Route Structure**:
```
Public Routes:
  /login       - User login
  /register    - User registration
  /pricing     - Pricing plans
  /health      - System health check

Protected Routes (require authentication):
  /            - Redirects to /dashboard
  /dashboard   - Main analytics dashboard
  /bi-dashboard - Business Intelligence dashboard
  /profile     - User profile and settings
  /affiliate   - Affiliate management
  /admin       - Admin panel (admin users only)
```

### 2. Layout Components

#### Layout (`components/Layout.tsx`)
Main layout wrapper that includes:
- Navbar (top)
- Sidebar (left)
- Content area (main)
- Outlet for nested routes

#### Navbar (`components/Navbar.tsx`)
Top navigation bar featuring:
- Logo and branding
- Quick actions
- User menu with dropdown
- Logout functionality

#### Sidebar (`components/Sidebar.tsx`)
Left navigation menu with:
- Main navigation links
- Active route highlighting
- Role-based menu items
- Expandable sections

### 3. Authentication System

#### AuthContext (`contexts/AuthContext.tsx`)
Centralized authentication state management:

**State**:
- `user`: Current user object
- `isAuthenticated`: Boolean auth status
- `isLoading`: Loading state

**Methods**:
- `login(email, password)`: Authenticate user
- `register(email, password, fullName)`: Create new account
- `logout()`: Clear session and redirect
- `refreshUser()`: Reload user data

**Features**:
- Automatic token storage (localStorage)
- Session persistence across page reloads
- Automatic redirect on 401 responses
- Error handling with toast notifications

#### PrivateRoute (`components/PrivateRoute.tsx`)
Route protection wrapper that:
- Checks authentication status
- Redirects to login if not authenticated
- Shows loading state during auth check
- Preserves intended route after login

### 4. API Layer (`lib/api.ts`)

Configured Axios instance with:

**Base Configuration**:
- Base URL from environment variable
- JSON content type
- Timeout handling

**Request Interceptor**:
- Adds JWT token to Authorization header
- Reads token from localStorage

**Response Interceptor**:
- Handles 401 unauthorized responses
- Auto-logout and redirect to login
- Error propagation

**Usage Example**:
```typescript
import { api } from '@/lib/api'

const fetchData = async () => {
  const response = await api.get('/api/v1/endpoint')
  return response.data
}
```

### 5. Real-time Features

#### WebSocket Hook (`hooks/useWebSocket.ts`)
Custom hook for WebSocket connections:

**Features**:
- Automatic connection management
- Event subscription/unsubscription
- Reconnection logic
- Connection status tracking

**Usage**:
```typescript
const { connected, subscribe } = useWebSocket()

useEffect(() => {
  const unsubscribe = subscribe('metric_update', (data) => {
    updateMetrics(data)
  })
  return unsubscribe
}, [])
```

## Page Components

### Dashboard Pages

#### Main Dashboard (`pages/Dashboard.tsx`)
Primary analytics dashboard featuring:
- Key performance indicators (KPIs)
- Real-time metrics updates
- Chart visualizations (Recharts)
- User activity feed
- Quick action buttons

**Data Sources**:
- `/api/v1/analytics/overview`
- WebSocket: `metric_update` events

#### BI Dashboard (`pages/BIDashboard.tsx`)
Business Intelligence dashboard with:
- Advanced analytics widgets
- Custom D3.js visualizations
- Data export functionality
- Interactive filters
- Drill-down capabilities

**Features**:
- Real-time data refresh
- Multiple visualization types
- Responsive grid layout
- Export to CSV/Excel

### User Pages

#### Login (`pages/Login.tsx`)
User authentication page:
- Email/password form
- Form validation
- Error display
- "Remember me" option
- Link to registration

#### Register (`pages/Register.tsx`)
New user registration:
- Multi-field form (email, password, name)
- Password strength indicator
- Terms acceptance
- Email verification flow
- Automatic login after registration

#### Profile (`pages/Profile.tsx`)
User profile management:
- Personal information editing
- Password change
- MFA setup
- Session management
- Account deletion

### Business Pages

#### Affiliate Dashboard (`pages/AffiliateDashboard.tsx`)
Affiliate program management:
- Referral link generation
- Commission tracking
- Performance metrics
- Payment history
- Marketing materials

#### Pricing (`pages/Pricing.tsx`)
Subscription plans display:
- Plan comparison table
- Feature highlights
- CTA buttons
- FAQ section
- Contact sales option

#### Admin Panel (`pages/AdminPanel.tsx`)
Administrative controls:
- User management
- System configuration
- Usage statistics
- Audit logs
- Feature flags

#### Health (`pages/Health.tsx`)
System health monitoring:
- Service status indicators
- Uptime metrics
- Recent incidents
- Performance graphs
- Dependency health

## Styling System

### CSS Variables (`index.css`)

Global design tokens defined as CSS variables:

**Colors**:
```css
--primary: #00ff88        /* Primary brand color */
--secondary: #6c63ff      /* Secondary accent */
--background: #0a0a0f     /* Dark background */
--surface: #1a1a2e        /* Card/surface background */
--text: #ffffff           /* Primary text */
--text-muted: #a0a0a0     /* Secondary text */
--border: rgba(0, 255, 136, 0.2)  /* Border color */
--error: #ff5555          /* Error state */
--success: #00ff88        /* Success state */
--warning: #ffaa00        /* Warning state */
```

**Spacing**:
```css
--spacing-xs: 0.25rem     /* 4px */
--spacing-sm: 0.5rem      /* 8px */
--spacing-md: 1rem        /* 16px */
--spacing-lg: 1.5rem      /* 24px */
--spacing-xl: 2rem        /* 32px */
```

**Typography**:
```css
--font-family: 'Inter', system-ui, sans-serif
--font-size-sm: 0.875rem  /* 14px */
--font-size-base: 1rem    /* 16px */
--font-size-lg: 1.125rem  /* 18px */
--font-size-xl: 1.5rem    /* 24px */
```

### Component Styling

**Pattern**: Component-scoped CSS with BEM naming:

```tsx
// Component.tsx
<div className="component">
  <div className="component__header">
    <h2 className="component__title">Title</h2>
  </div>
  <div className="component__content">
    Content
  </div>
</div>
```

```css
.component {
  background: var(--surface);
  border-radius: 8px;
  padding: var(--spacing-md);
}

.component__header {
  border-bottom: 1px solid var(--border);
  padding-bottom: var(--spacing-sm);
}

.component__title {
  color: var(--primary);
  font-size: var(--font-size-xl);
}
```

### Responsive Design

Mobile-first approach with breakpoints:

```css
/* Mobile: Default styles */
.container {
  padding: var(--spacing-md);
}

/* Tablet: 768px and up */
@media (min-width: 768px) {
  .container {
    padding: var(--spacing-lg);
  }
}

/* Desktop: 1024px and up */
@media (min-width: 1024px) {
  .container {
    padding: var(--spacing-xl);
    max-width: 1200px;
    margin: 0 auto;
  }
}
```

## State Management

### Context API (Authentication)

Used for global authentication state:
- User information
- Auth status
- Login/logout actions

**Benefits**:
- Simple, built-in solution
- No additional dependencies
- Good for infrequent updates

### Component State (useState)

Used for local component state:
- Form inputs
- UI toggles
- Loading states
- Temporary data

### Zustand (Optional, for complex state)

For complex state management needs:
```typescript
import create from 'zustand'

interface AppState {
  theme: 'light' | 'dark'
  setTheme: (theme: 'light' | 'dark') => void
}

const useAppStore = create<AppState>((set) => ({
  theme: 'dark',
  setTheme: (theme) => set({ theme })
}))
```

## Data Flow

### 1. Initial Load
```
User Opens App
  → App.tsx renders
  → AuthProvider checks localStorage
  → API call to /api/v1/auth/me
  → Set user state
  → Render appropriate route
```

### 2. API Request
```
Component mounts
  → useEffect runs
  → api.get() call
  → Request interceptor adds token
  → API responds
  → Response interceptor handles errors
  → Component updates state
  → Re-render with data
```

### 3. Real-time Update
```
Component subscribes to WebSocket
  → Server sends event
  → useWebSocket hook receives event
  → Callback function executes
  → Component state updates
  → Re-render with new data
```

### 4. User Action
```
User clicks button
  → Event handler fires
  → API call (POST/PUT/DELETE)
  → Loading state set
  → Response received
  → State updated
  → Toast notification shown
  → Data refreshed
```

## Build and Deployment

### Development

```bash
npm run dev
```

Starts Vite dev server on `http://localhost:5173` with:
- Hot Module Replacement (HMR)
- Fast refresh
- Source maps
- Error overlay

### Production Build

```bash
npm run build
```

Outputs to `dist/` directory:
- TypeScript compilation
- Asset optimization
- Code splitting
- Minification
- Source maps (optional)

### Docker Deployment

Multi-stage Docker build:

**Stage 1: Build**
- Install dependencies
- Build TypeScript
- Create production bundle

**Stage 2: Runtime**
- Nginx web server
- Serve static files
- Reverse proxy to backend
- HTTPS configuration

### Environment Variables

Set via `.env` file or build arguments:

```bash
VITE_API_URL=https://api.example.com
VITE_WS_URL=wss://api.example.com
VITE_ENV=production
```

Access in code:
```typescript
const apiUrl = import.meta.env.VITE_API_URL
```

## Performance Optimization

### Code Splitting

Lazy load routes:
```typescript
const Dashboard = lazy(() => import('./pages/Dashboard'))

<Suspense fallback={<Loading />}>
  <Dashboard />
</Suspense>
```

### Asset Optimization

- Image compression
- SVG optimization
- Font subsetting
- CSS minification

### Caching

```nginx
# nginx.conf
location /assets {
  expires 1y;
  add_header Cache-Control "public, immutable";
}
```

### Bundle Analysis

```bash
npm run build -- --mode analyze
```

View bundle composition and identify optimization opportunities.

## Testing Strategy

### Unit Tests

Test individual components:
```bash
npm run test
```

### Integration Tests

Test component interactions and API calls.

### E2E Tests

Test complete user flows (Cypress/Playwright).

### Coverage

Aim for:
- 80%+ code coverage
- Critical paths tested
- Error cases covered

## Security Considerations

### XSS Prevention

- React auto-escapes content
- Avoid `dangerouslySetInnerHTML`
- Sanitize user input

### CSRF Protection

- SameSite cookies
- CSRF tokens for forms
- Validate origin headers

### Token Storage

**Current**: localStorage (convenient but vulnerable to XSS)

**Better**: httpOnly cookies (protected from JavaScript access)

**Best**: httpOnly cookies + SameSite + Secure flags

### Content Security Policy

```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline'; 
               style-src 'self' 'unsafe-inline';">
```

## Accessibility

### ARIA Labels

```tsx
<button aria-label="Close dialog">×</button>
```

### Keyboard Navigation

- Tab order
- Focus management
- Keyboard shortcuts

### Screen Reader Support

- Semantic HTML
- ARIA roles
- Alt text for images

### Color Contrast

- WCAG AA compliance
- 4.5:1 ratio for text
- Test with tools

## Best Practices

### Component Design

1. **Single Responsibility**: One component, one purpose
2. **Props Interface**: TypeScript interfaces for all props
3. **Error Boundaries**: Catch and handle errors gracefully
4. **Loading States**: Show feedback during async operations
5. **Error States**: Display meaningful error messages

### Code Organization

1. **Folder Structure**: Group related files
2. **Naming Conventions**: PascalCase for components, camelCase for utilities
3. **Import Order**: React → Third-party → Local
4. **File Size**: Keep components under 300 lines

### Performance

1. **Memoization**: Use `useMemo` and `useCallback` for expensive operations
2. **Lazy Loading**: Code split routes and heavy components
3. **Virtual Scrolling**: For long lists (react-window)
4. **Debouncing**: For search inputs and frequent updates

### Type Safety

1. **Strict Mode**: Enable strict TypeScript checks
2. **No Any**: Avoid `any` type, use `unknown` or proper types
3. **Interface Over Type**: Prefer `interface` for object shapes
4. **Enum for Constants**: Use enums for fixed sets of values

## Troubleshooting

### Common Issues

**Build Fails**:
- Clear node_modules and reinstall
- Check TypeScript errors
- Verify environment variables

**API Calls Fail**:
- Check CORS configuration
- Verify API URL
- Check network tab in DevTools

**Hot Reload Not Working**:
- Restart dev server
- Check file watching limits
- Clear browser cache

### Debug Tools

- React DevTools
- Redux DevTools (if using Redux)
- Network tab (Chrome DevTools)
- Console logs

## Future Enhancements

### Planned Features

1. **Progressive Web App (PWA)**: Offline support, push notifications
2. **Internationalization (i18n)**: Multi-language support
3. **Theme Switching**: Light/dark mode toggle
4. **Advanced Analytics**: User behavior tracking
5. **A/B Testing**: Feature flag system

### Technical Debt

1. **Migration to Tanstack Query**: Better data fetching and caching
2. **Component Library**: Create shared component library
3. **Storybook**: Component documentation and testing
4. **E2E Tests**: Comprehensive test coverage

## Related Documentation

- [Frontend README](./README.md) - Setup and quick start
- [Backend API Documentation](../backend/README.md) - API endpoints
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment
- [Component Guide](./COMPONENTS.md) - Component usage examples

## Support

For issues or questions:
1. Check this documentation
2. Review component source code
3. Check browser console for errors
4. Review API responses in Network tab
