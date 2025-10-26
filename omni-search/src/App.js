import React, { Suspense, useState } from 'react';

// Lazy-loaded modules
const ChatModule = React.lazy(() => import('./modules/ChatModule'));
const QuantumLab = React.lazy(() => import('./modules/QuantumLab'));
const VRStudio = React.lazy(() => import('./modules/VRStudio'));
const Analytics = React.lazy(() => import('./modules/Analytics'));

// Simple Sidebar navigation
const Sidebar = ({ current, onNavigate }) => {
  const items = [
    { key: 'chat', label: 'AI Chat' },
    { key: 'quantum', label: 'Quantum Lab' },
    { key: 'vr', label: 'VR Studio' },
    { key: 'analytics', label: 'Analytics' },
  ];
  return (
    <div style={{ width: 220, background: '#0f172a', color: '#e2e8f0', padding: 12 }}>
      <div style={{ fontWeight: 700, marginBottom: 12 }}>OMNI Dashboard</div>
      {items.map((it) => (
        <div
          key={it.key}
          onClick={() => onNavigate(it.key)}
          style={{
            padding: '8px 10px',
            cursor: 'pointer',
            borderRadius: 6,
            background: current === it.key ? '#1f2937' : 'transparent',
            marginBottom: 6,
          }}
        >
          {it.label}
        </div>
      ))}
    </div>
  );
};

export default function App() {
  const [route, setRoute] = useState('chat');

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0b1020' }}>
      <Sidebar current={route} onNavigate={setRoute} />
      <div style={{ flex: 1, padding: 16, color: '#f8fafc' }}>
        <Suspense fallback={<div>Loading module...</div>}>
          {route === 'chat' && <ChatModule />}
          {route === 'quantum' && <QuantumLab />}
          {route === 'vr' && <VRStudio />}
          {route === 'analytics' && <Analytics />}
        </Suspense>
      </div>
    </div>
  );
}