export default function SettingsPage() {
  const backend = process.env.REACT_APP_BACKEND_URL || '(dev proxy to http://localhost:3001)';
  const openai = process.env.OPENAI_API_KEY ? 'configured' : 'not set';
  const gemini = process.env.GEMINI_API_KEY ? 'configured' : 'not set';

  return (
    <div className="p-4 text-gray-200 dark:text-gray-900">
      <h2 className="text-2xl font-bold mb-2">Nastavitve</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-3 rounded-lg border border-gray-800 bg-black/30 dark:bg-white">
          <h3 className="font-mono text-sm mb-2">Backend URL</h3>
          <p className="text-sm">{backend}</p>
          <p className="text-xs text-gray-400">Set REACT_APP_BACKEND_URL to override.</p>
        </div>
        <div className="p-3 rounded-lg border border-gray-800 bg-black/30 dark:bg-white">
          <h3 className="font-mono text-sm mb-2">API Keys</h3>
          <p className="text-sm">OpenAI: {openai}</p>
          <p className="text-sm">Gemini: {gemini}</p>
          <p className="text-xs text-gray-400">Add keys to .env or system env for full capabilities.</p>
        </div>
      </div>
    </div>
  );
}