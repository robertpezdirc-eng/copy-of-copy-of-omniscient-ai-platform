import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import Sidebar from './Sidebar'

const Layout = () => {
  return (
    <div style={styles.container}>
      <Navbar />
      <div style={styles.content}>
        <Sidebar />
        <main style={styles.main}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
  },
  content: {
    display: 'flex',
    flex: 1,
  },
  main: {
    flex: 1,
    padding: '24px',
    overflowY: 'auto',
  },
}

export default Layout
