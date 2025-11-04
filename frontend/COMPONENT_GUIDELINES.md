# Frontend Component Development Guidelines

## Overview

This document provides guidelines and best practices for developing React components in the Omni Enterprise Ultra Max frontend application.

## Component Structure

### File Organization

```
src/components/
├── common/              # Shared/reusable components
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx
│   │   └── index.ts
│   ├── Input/
│   │   ├── Input.tsx
│   │   └── index.ts
│   └── ...
├── dashboard/           # Dashboard-specific components
│   ├── D3Visualizations.tsx
│   └── RealTimeMetrics.tsx
├── Layout.tsx
├── Navbar.tsx
└── Sidebar.tsx
```

### Component Template

```typescript
/**
 * ComponentName - Brief description
 * 
 * @example
 * <ComponentName prop1="value" prop2={42} />
 */

import { useState } from 'react'
import type { ComponentProps } from '@/types'

interface ComponentNameProps {
  /** Prop description */
  prop1: string
  /** Optional prop with default */
  prop2?: number
  /** Callback function */
  onAction?: (data: any) => void
  /** Children components */
  children?: React.ReactNode
}

export function ComponentName({
  prop1,
  prop2 = 0,
  onAction,
  children,
}: ComponentNameProps) {
  const [state, setState] = useState<string>('')

  const handleClick = () => {
    onAction?.(state)
  }

  return (
    <div>
      {/* Component JSX */}
      {children}
    </div>
  )
}

export default ComponentName
```

## Component Types

### 1. Presentational Components

**Purpose**: Display data, no business logic

```typescript
interface UserCardProps {
  user: User
  onEdit?: () => void
}

export function UserCard({ user, onEdit }: UserCardProps) {
  return (
    <div className="card">
      <h3>{user.full_name}</h3>
      <p>{user.email}</p>
      {onEdit && <button onClick={onEdit}>Edit</button>}
    </div>
  )
}
```

### 2. Container Components

**Purpose**: Manage state and business logic

```typescript
export function UserListContainer() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchUsers() {
      try {
        const data = await userService.list()
        setUsers(data.items)
      } catch (error) {
        console.error(error)
      } finally {
        setLoading(false)
      }
    }
    fetchUsers()
  }, [])

  if (loading) return <LoadingSpinner />

  return (
    <div>
      {users.map(user => (
        <UserCard key={user.id} user={user} />
      ))}
    </div>
  )
}
```

### 3. Layout Components

**Purpose**: Define page structure

```typescript
interface LayoutProps {
  children: React.ReactNode
  title?: string
}

export function Layout({ children, title }: LayoutProps) {
  return (
    <div className="layout">
      <Navbar />
      <Sidebar />
      <main>
        {title && <h1>{title}</h1>}
        {children}
      </main>
    </div>
  )
}
```

## Best Practices

### 1. Props Interface

✅ **DO**: Define explicit props interface

```typescript
interface ButtonProps {
  text: string
  variant?: 'primary' | 'secondary'
  onClick: () => void
  disabled?: boolean
}

export function Button({ text, variant = 'primary', onClick, disabled }: ButtonProps) {
  // ...
}
```

❌ **DON'T**: Use inline types

```typescript
// Avoid this
export function Button({ text, onClick }: { text: string; onClick: () => void }) {
  // ...
}
```

### 2. Default Props

✅ **DO**: Use default parameters

```typescript
interface Props {
  size?: 'small' | 'medium' | 'large'
  color?: string
}

export function Component({ size = 'medium', color = '#000' }: Props) {
  // ...
}
```

### 3. State Management

✅ **DO**: Use typed state

```typescript
import type { User } from '@/types'

const [user, setUser] = useState<User | null>(null)
const [loading, setLoading] = useState<boolean>(false)
const [error, setError] = useState<Error | null>(null)
```

✅ **DO**: Use AsyncState for API calls

```typescript
import type { AsyncState, User } from '@/types'

const [userState, setUserState] = useState<AsyncState<User>>({
  data: null,
  loading: true,
  error: null,
})
```

### 4. Event Handlers

✅ **DO**: Type event handlers properly

```typescript
const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  setValue(e.target.value)
}

const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault()
  // ...
}

const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
  e.stopPropagation()
  // ...
}
```

### 5. Children Props

✅ **DO**: Use React.ReactNode for children

```typescript
interface Props {
  children: React.ReactNode
}

export function Container({ children }: Props) {
  return <div>{children}</div>
}
```

### 6. Conditional Rendering

✅ **DO**: Use early returns

```typescript
export function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Fetch user...

  if (loading) return <LoadingSpinner />
  if (!user) return <NotFound />

  return (
    <div>
      <h1>{user.full_name}</h1>
      {/* ... */}
    </div>
  )
}
```

### 7. Custom Hooks

✅ **DO**: Extract reusable logic

```typescript
// hooks/useUser.ts
export function useUser(userId: string) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    async function fetchUser() {
      try {
        const data = await userService.getById(userId)
        setUser(data)
      } catch (err) {
        setError(err as Error)
      } finally {
        setLoading(false)
      }
    }
    fetchUser()
  }, [userId])

  return { user, loading, error }
}

// Usage
export function UserProfile({ userId }: { userId: string }) {
  const { user, loading, error } = useUser(userId)
  
  if (loading) return <LoadingSpinner />
  if (error) return <ErrorMessage error={error} />
  if (!user) return <NotFound />
  
  return <div>{user.full_name}</div>
}
```

## Styling

### Inline Styles (Current Approach)

```typescript
const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '1rem',
    padding: '2rem',
  },
  title: {
    fontSize: '2rem',
    fontWeight: 'bold',
    color: COLORS.text.primary,
  },
} as const

export function Component() {
  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Title</h1>
    </div>
  )
}
```

### CSS Classes

```typescript
import './Component.css'

export function Component() {
  return (
    <div className="component-container">
      <h1 className="component-title">Title</h1>
    </div>
  )
}
```

### Dynamic Styles

```typescript
import { COLORS } from '@/constants'
import clsx from 'clsx'

interface ButtonProps {
  variant: 'primary' | 'secondary'
  size: 'small' | 'medium' | 'large'
}

export function Button({ variant, size }: ButtonProps) {
  const className = clsx(
    'button',
    `button--${variant}`,
    `button--${size}`
  )

  const style = {
    backgroundColor: variant === 'primary' ? COLORS.primary : COLORS.secondary,
  }

  return (
    <button className={className} style={style}>
      Click me
    </button>
  )
}
```

## Loading States

### Pattern 1: Simple Loading

```typescript
export function Component() {
  const [loading, setLoading] = useState(true)

  if (loading) {
    return <div>Loading...</div>
  }

  return <div>Content</div>
}
```

### Pattern 2: Skeleton Loading

```typescript
export function UserCard({ userId }: { userId: string }) {
  const { user, loading } = useUser(userId)

  if (loading) {
    return (
      <div className="card">
        <div className="skeleton skeleton-title" />
        <div className="skeleton skeleton-text" />
        <div className="skeleton skeleton-text" />
      </div>
    )
  }

  return (
    <div className="card">
      <h3>{user!.full_name}</h3>
      <p>{user!.email}</p>
    </div>
  )
}
```

### Pattern 3: Suspense (Future)

```typescript
import { Suspense } from 'react'

export function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <UserProfile userId="123" />
    </Suspense>
  )
}
```

## Error Handling

### Pattern 1: Error State

```typescript
export function Component() {
  const [error, setError] = useState<Error | null>(null)

  if (error) {
    return (
      <div className="error">
        <p>Error: {error.message}</p>
        <button onClick={() => setError(null)}>Retry</button>
      </div>
    )
  }

  return <div>Content</div>
}
```

### Pattern 2: Error Boundary (Recommended)

```typescript
// components/ErrorBoundary.tsx
import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
        </div>
      )
    }

    return this.props.children
  }
}

// Usage
export function App() {
  return (
    <ErrorBoundary>
      <MyComponent />
    </ErrorBoundary>
  )
}
```

## Forms

### Pattern 1: Controlled Components

```typescript
import { useState } from 'react'
import { isValidEmail } from '@/utils'

export function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})

  const validate = () => {
    const newErrors: Record<string, string> = {}
    
    if (!isValidEmail(email)) {
      newErrors.email = 'Invalid email address'
    }
    
    if (password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validate()) return
    
    try {
      await authService.login({ email, password })
    } catch (error) {
      // Handle error
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
        />
        {errors.email && <span className="error">{errors.email}</span>}
      </div>
      
      <div>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
        />
        {errors.password && <span className="error">{errors.password}</span>}
      </div>
      
      <button type="submit">Login</button>
    </form>
  )
}
```

### Pattern 2: Form Hook

```typescript
// hooks/useForm.ts
import { useState } from 'react'

export function useForm<T extends Record<string, any>>(initialValues: T) {
  const [values, setValues] = useState<T>(initialValues)
  const [errors, setErrors] = useState<Record<keyof T, string>>({} as any)

  const handleChange = (name: keyof T) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setValues({ ...values, [name]: e.target.value })
    // Clear error when user types
    if (errors[name]) {
      setErrors({ ...errors, [name]: '' })
    }
  }

  const reset = () => {
    setValues(initialValues)
    setErrors({} as any)
  }

  return { values, errors, setErrors, handleChange, reset }
}

// Usage
export function LoginForm() {
  const { values, errors, setErrors, handleChange } = useForm({
    email: '',
    password: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    // Validate and submit
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={values.email}
        onChange={handleChange('email')}
      />
      {errors.email && <span>{errors.email}</span>}
      
      <input
        type="password"
        value={values.password}
        onChange={handleChange('password')}
      />
      {errors.password && <span>{errors.password}</span>}
      
      <button type="submit">Login</button>
    </form>
  )
}
```

## Performance Optimization

### 1. Memoization

```typescript
import { useMemo } from 'react'

export function ExpensiveComponent({ data }: { data: number[] }) {
  const sorted = useMemo(() => {
    console.log('Sorting...')
    return [...data].sort((a, b) => a - b)
  }, [data])

  return <div>{sorted.join(', ')}</div>
}
```

### 2. useCallback

```typescript
import { useCallback } from 'react'

export function Parent() {
  const [count, setCount] = useState(0)

  const handleClick = useCallback(() => {
    setCount(c => c + 1)
  }, [])

  return <Child onClick={handleClick} />
}
```

### 3. React.memo

```typescript
import { memo } from 'react'

interface Props {
  user: User
}

const UserCard = memo(function UserCard({ user }: Props) {
  return (
    <div>
      <h3>{user.full_name}</h3>
      <p>{user.email}</p>
    </div>
  )
})

export default UserCard
```

## Testing

### Component Test Example

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from './Button'

describe('Button', () => {
  it('renders with text', () => {
    render(<Button text="Click me" onClick={() => {}} />)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const onClick = jest.fn()
    render(<Button text="Click me" onClick={onClick} />)
    
    fireEvent.click(screen.getByText('Click me'))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button text="Click me" onClick={() => {}} disabled />)
    expect(screen.getByText('Click me')).toBeDisabled()
  })
})
```

## Accessibility

### 1. Semantic HTML

✅ **DO**: Use semantic elements

```typescript
<nav>
  <ul>
    <li><a href="/">Home</a></li>
  </ul>
</nav>

<main>
  <article>
    <h1>Title</h1>
    <p>Content</p>
  </article>
</main>

<footer>
  <p>&copy; 2025</p>
</footer>
```

### 2. ARIA Attributes

```typescript
<button
  aria-label="Close dialog"
  aria-pressed={isActive}
  onClick={handleClose}
>
  ×
</button>

<input
  type="text"
  aria-label="Search"
  aria-describedby="search-help"
/>
<div id="search-help">Enter keywords to search</div>
```

### 3. Keyboard Navigation

```typescript
export function Modal({ isOpen, onClose }: ModalProps) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, onClose])

  return isOpen ? <div>{/* Modal content */}</div> : null
}
```

## Common Patterns

### 1. Data Fetching

```typescript
export function UserList() {
  const [state, setState] = useState<AsyncState<User[]>>({
    data: null,
    loading: true,
    error: null,
  })

  useEffect(() => {
    let cancelled = false

    async function fetchData() {
      try {
        const users = await userService.list()
        if (!cancelled) {
          setState({ data: users.items, loading: false, error: null })
        }
      } catch (error) {
        if (!cancelled) {
          setState({ data: null, loading: false, error: error as Error })
        }
      }
    }

    fetchData()

    return () => {
      cancelled = true
    }
  }, [])

  if (state.loading) return <LoadingSpinner />
  if (state.error) return <ErrorMessage error={state.error} />
  if (!state.data) return null

  return (
    <div>
      {state.data.map(user => (
        <UserCard key={user.id} user={user} />
      ))}
    </div>
  )
}
```

### 2. Pagination

```typescript
export function PaginatedList() {
  const [page, setPage] = useState(1)
  const [data, setData] = useState<User[]>([])
  const [total, setTotal] = useState(0)

  const perPage = 20

  useEffect(() => {
    async function fetchData() {
      const result = await userService.list({ page, per_page: perPage })
      setData(result.items)
      setTotal(result.total)
    }
    fetchData()
  }, [page])

  return (
    <div>
      <div>
        {data.map(user => (
          <UserCard key={user.id} user={user} />
        ))}
      </div>
      
      <div>
        <button
          disabled={page === 1}
          onClick={() => setPage(p => p - 1)}
        >
          Previous
        </button>
        
        <span>Page {page} of {Math.ceil(total / perPage)}</span>
        
        <button
          disabled={page >= Math.ceil(total / perPage)}
          onClick={() => setPage(p => p + 1)}
        >
          Next
        </button>
      </div>
    </div>
  )
}
```

### 3. Modal/Dialog

```typescript
export function Modal({
  isOpen,
  onClose,
  title,
  children,
}: {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
}) {
  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button onClick={onClose}>×</button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  )
}
```

## Summary

Follow these guidelines to maintain consistency and quality across all components:

1. ✅ Use TypeScript with proper types
2. ✅ Define explicit props interfaces
3. ✅ Use typed state and event handlers
4. ✅ Extract reusable logic into custom hooks
5. ✅ Handle loading and error states
6. ✅ Use error boundaries for error handling
7. ✅ Optimize performance with memoization
8. ✅ Write accessible components
9. ✅ Test components thoroughly
10. ✅ Follow consistent naming and structure

These patterns ensure maintainable, type-safe, and user-friendly components.
