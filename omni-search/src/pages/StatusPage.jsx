import { useEffect, useState } from 'react';

export default function StatusPage() {
  const [agents, setAgents] = useState(null);
  const [platform, setPlatform] = useState(null);
  const base = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    const run = async () => {
      try {
        const a = await fetch(`${base}/api/agents/status`);
        if (a.ok) setAgents(await a.json());
      } catch {}
      try {
        const p = await fetch(`${base}/api/platform/status`);
        if (p.ok) setPlatform(await p.json());
      } catch {}
    };
    run();
  }, [base]);

  return (
    <div className="p-4 text-gray-200 dark:text-gray-900">
      <h2 className="text-2xl font-bold mb-2">Platform Status</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-3 rounded-lg border border-gray-800 bg-black/30 dark:bg-white">
          <h3 className="font-mono text-sm mb-2">Agents</h3>
          <pre className="text-xs whitespace-pre-wrap">{agents ? JSON.stringify(agents, null, 2) : 'Loading...'}</pre>
        </div>
        <div className="p-3 rounded-lg border border-gray-800 bg-black/30 dark:bg-white">
          <h3 className="font-mono text-sm mb-2">Platform</h3>
          <pre className="text-xs whitespace-pre-wrap">{platform ? JSON.stringify(platform, null, 2) : 'Loading...'}</pre>
        </div>
      </div>
    </div>
  );
}