/**
 * LoadingSpinner - Reusable loading indicator
 * 
 * @example
 * <LoadingSpinner size="large" message="Loading data..." />
 */

import { COLORS } from '@/constants'

interface LoadingSpinnerProps {
  /** Size of the spinner */
  size?: 'small' | 'medium' | 'large'
  /** Optional loading message */
  message?: string
  /** Show full page overlay */
  fullPage?: boolean
}

const sizeMap = {
  small: 24,
  medium: 48,
  large: 72,
}

export function LoadingSpinner({
  size = 'medium',
  message,
  fullPage = false,
}: LoadingSpinnerProps) {
  const spinnerSize = sizeMap[size]

  const content = (
    <div style={fullPage ? styles.fullPageContainer : styles.container}>
      <div
        style={{
          ...styles.spinner,
          width: spinnerSize,
          height: spinnerSize,
          borderWidth: spinnerSize / 12,
        }}
      />
      {message && <p style={styles.message}>{message}</p>}
    </div>
  )

  if (fullPage) {
    return (
      <div style={styles.overlay}>
        {content}
      </div>
    )
  }

  return content
}

const styles = {
  overlay: {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(10, 10, 15, 0.8)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
  },
  fullPageContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    gap: '1rem',
  },
  container: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    gap: '1rem',
    padding: '2rem',
  },
  spinner: {
    border: `4px solid rgba(255, 255, 255, 0.1)`,
    borderTop: `4px solid ${COLORS.primary}`,
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  message: {
    color: COLORS.text.secondary,
    fontSize: '1rem',
    marginTop: '0.5rem',
    textAlign: 'center' as const,
  },
}

// Add keyframes animation to document if not already present
if (typeof document !== 'undefined') {
  const styleSheet = document.styleSheets[0]
  const keyframes = `
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `
  
  try {
    styleSheet.insertRule(keyframes, styleSheet.cssRules.length)
  } catch (e) {
    // Animation might already exist
  }
}

export default LoadingSpinner
