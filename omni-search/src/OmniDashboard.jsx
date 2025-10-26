import { useState } from 'react';
import TopNav from './components/TopNav';
import StatusPage from './pages/StatusPage';
import GeminiStreamPage from './pages/GeminiStreamPage';
import ModulesPage from './pages/ModulesPage';
import SettingsPage from './pages/SettingsPage';
import './index.css';

export default function OmniDashboard() {
  const [page, setPage] = useState('status');

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 dark:from-gray-100 dark:via-white dark:to-gray-100">
      <TopNav active={page} onChange={setPage} />
      {page === 'status' && <StatusPage />}
      {page === 'gemini' && <GeminiStreamPage />}
      {page === 'modules' && <ModulesPage />}
      {page === 'settings' && <SettingsPage />}
    </div>
  );
}