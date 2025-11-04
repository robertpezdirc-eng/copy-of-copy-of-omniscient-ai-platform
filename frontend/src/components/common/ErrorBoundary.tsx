/**
 * ErrorBoundary - Catches and handles React component errors
 * 
 * @example
 * <ErrorBoundary fallback={<ErrorPage />}>
 *   <App />
 * </ErrorBoundary>
 */

import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error?: Error
  errorInfo?: ErrorInfo
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
    
    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo)
    
    this.setState({ errorInfo })
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined })
  }

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default error UI
      return (
        <div style={styles.container}>
          <div style={styles.content}>
            <h1 style={styles.title}>⚠️ Something went wrong</h1>
            <p style={styles.message}>
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            
            {import.meta.env.DEV && this.state.errorInfo && (
              <details style={styles.details}>
                <summary style={styles.summary}>Error Details</summary>
                <pre style={styles.stack}>
                  {this.state.error?.stack}
                </pre>
                <pre style={styles.stack}>
                  {this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
            
            <button style={styles.button} onClick={this.handleReset}>
              Try Again
            </button>
            
            <button
              style={{ ...styles.button, ...styles.buttonSecondary }}
              onClick={() => window.location.href = '/'}
            >
              Go to Home
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

const styles = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    backgroundColor: '#0a0a0f',
    padding: '2rem',
  },
  content: {
    maxWidth: '600px',
    width: '100%',
    padding: '2rem',
    backgroundColor: '#1a1a2e',
    borderRadius: '8px',
    border: '1px solid rgba(255, 85, 85, 0.3)',
    textAlign: 'center' as const,
  },
  title: {
    fontSize: '2rem',
    fontWeight: 'bold',
    color: '#ff5555',
    marginBottom: '1rem',
  },
  message: {
    fontSize: '1.125rem',
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: '2rem',
    lineHeight: 1.6,
  },
  details: {
    marginTop: '2rem',
    marginBottom: '2rem',
    textAlign: 'left' as const,
    backgroundColor: '#0a0a0f',
    padding: '1rem',
    borderRadius: '4px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
  },
  summary: {
    cursor: 'pointer',
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: '1rem',
    fontWeight: 'bold',
  },
  stack: {
    fontSize: '0.875rem',
    color: 'rgba(255, 255, 255, 0.6)',
    overflow: 'auto',
    maxHeight: '300px',
    whiteSpace: 'pre-wrap' as const,
    wordWrap: 'break-word' as const,
  },
  button: {
    padding: '0.75rem 1.5rem',
    fontSize: '1rem',
    fontWeight: 'bold',
    color: '#fff',
    backgroundColor: '#00ff88',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    margin: '0.5rem',
    transition: 'all 0.2s',
  },
  buttonSecondary: {
    backgroundColor: 'transparent',
    border: '1px solid rgba(255, 255, 255, 0.3)',
  },
}

export default ErrorBoundary
