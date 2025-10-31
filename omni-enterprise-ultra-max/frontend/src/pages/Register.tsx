import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

const Register = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      await register(email, password, fullName)
      navigate('/login')
    } catch (error) {
      // Error handled in AuthContext
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 className="gradient-text" style={styles.title}>
          Create Account
        </h1>
        <p style={styles.subtitle}>Join Omni Enterprise Ultra Max</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.field}>
            <label style={styles.label}>Full Name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              style={styles.input}
              placeholder="John Doe"
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={styles.input}
              placeholder="your@email.com"
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={styles.input}
              placeholder="••••••••"
              minLength={8}
            />
          </div>

          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <p style={styles.footer}>
          Already have an account?{' '}
          <Link to="/login" style={styles.link}>
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '24px',
  },
  card: {
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '24px',
    padding: '48px',
    backdropFilter: 'blur(10px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    width: '100%',
    maxWidth: '440px',
  },
  title: {
    fontSize: '32px',
    fontWeight: 'bold',
    marginBottom: '8px',
    textAlign: 'center',
  },
  subtitle: {
    color: 'var(--text-secondary)',
    textAlign: 'center',
    marginBottom: '32px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  label: {
    fontSize: '14px',
    fontWeight: '500',
    color: 'var(--text)',
  },
  input: {
    width: '100%',
  },
  button: {
    background: 'linear-gradient(90deg, var(--primary), var(--secondary))',
    color: '#000',
    padding: '14px',
    borderRadius: '12px',
    fontSize: '16px',
    fontWeight: 'bold',
    marginTop: '8px',
    transition: 'transform 0.2s',
  },
  footer: {
    textAlign: 'center',
    marginTop: '24px',
    color: 'var(--text-secondary)',
    fontSize: '14px',
  },
  link: {
    color: 'var(--primary)',
    fontWeight: '500',
  },
}

export default Register
