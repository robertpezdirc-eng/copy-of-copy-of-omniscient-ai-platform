import React from 'react'

const Pricing: React.FC = () => {
  return (
    <div style={styles.container}>
      <h1 className="gradient-text" style={styles.title}>Pricing</h1>
      <p style={styles.subtitle}>Choose the plan that fits your needs</p>

      <div style={styles.grid}>
        <div className="card" style={styles.card}>
          <h2 style={styles.cardTitle}>Starter</h2>
          <div style={styles.price}>€19<span style={styles.pricePeriod}>/mo</span></div>
          <ul style={styles.features}>
            <li>10k API calls</li>
            <li>Basic analytics</li>
            <li>Email support</li>
          </ul>
          <button style={styles.button}>Get Started</button>
        </div>

        <div className="card" style={styles.card}>
          <h2 style={styles.cardTitle}>Pro</h2>
          <div style={styles.price}>€99<span style={styles.pricePeriod}>/mo</span></div>
          <ul style={styles.features}>
            <li>250k API calls</li>
            <li>Advanced analytics</li>
            <li>Priority support</li>
          </ul>
          <button style={styles.button}>Upgrade</button>
        </div>

        <div className="card" style={styles.card}>
          <h2 style={styles.cardTitle}>Enterprise</h2>
          <div style={styles.price}>Custom</div>
          <ul style={styles.features}>
            <li>Unlimited API calls</li>
            <li>Dedicated cluster</li>
            <li>24/7 support</li>
          </ul>
          <button style={styles.button}>Contact Sales</button>
        </div>
      </div>
    </div>
  )
}

const styles: { [key: string]: React.CSSProperties } = {
  container: { maxWidth: '1200px', margin: '0 auto' },
  title: { fontSize: '36px', fontWeight: 'bold', marginBottom: '8px' },
  subtitle: { color: 'var(--text-secondary)', marginBottom: '24px' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px' },
  card: { padding: '24px', minHeight: '360px' },
  cardTitle: { fontSize: '20px', fontWeight: 'bold', marginBottom: '12px' },
  price: { fontSize: '32px', fontWeight: 'bold', color: 'var(--primary)', marginBottom: '12px' },
  pricePeriod: { fontSize: '14px', color: 'var(--text-secondary)' },
  features: { display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' },
  button: { background: 'linear-gradient(90deg, var(--primary), var(--secondary))', color: '#000', padding: '10px', borderRadius: '8px', fontWeight: 'bold' },
}

export default Pricing
