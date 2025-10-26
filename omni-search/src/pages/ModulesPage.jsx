import { useState } from 'react';

const DEFAULT_MODULES = [
  { name: 'ai_generator', actions: ['generate_text', 'generate_image'] },
  { name: 'data_analyzer', actions: ['summary', 'stats'] },
  { name: 'security', actions: ['scan', 'report'] },
];

export default function ModulesPage() {
  const [moduleName, setModuleName] = useState(DEFAULT_MODULES[0].name);
  const [action, setAction] = useState(DEFAULT_MODULES[0].actions[0]);
  const [params, setParams] = useState('{}');
  const [result, setResult] = useState(null);
  const base = process.env.REACT_APP_BACKEND_URL || '';

  const invoke = async () => {
    try {
      const res = await fetch(`${base}/api/modules/invoke`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module: moduleName, action, params: JSON.parse(params || '{}') })
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setResult({ ok: false, error: e.message });
    }
  };

  const selected = DEFAULT_MODULES.find(m => m.name === moduleName);

  return (
    <div className="p-4 text-gray-200 dark:text-gray-900">
      <h2 className="text-2xl font-bold mb-2">Klici modulov</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
        <select value={moduleName} onChange={e=>{ setModuleName(e.target.value); setAction(DEFAULT_MODULES.find(m=>m.name===e.target.value).actions[0]); }}
                className="px-3 py-2 rounded bg-gray-900 text-white border border-gray-700 dark:bg-white dark:text-black dark:border-gray-300">
          {DEFAULT_MODULES.map(m => <option key={m.name} value={m.name}>{m.name}</option>)}
        </select>
        <select value={action} onChange={e=>setAction(e.target.value)} className="px-3 py-2 rounded bg-gray-900 text-white border border-gray-700 dark:bg-white dark:text-black dark:border-gray-300">
          {selected.actions.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
        <input value={params} onChange={e=>setParams(e.target.value)} placeholder='{"prompt":"Hello"}'
               className="px-3 py-2 rounded bg-gray-900 text-white border border-gray-700 dark:bg-white dark:text-black dark:border-gray-300" />
      </div>
      <button onClick={invoke} className="px-3 py-2 rounded bg-green-600 text-white">Invoke</button>
      <div className="p-3 rounded-lg border border-gray-800 bg-black/30 dark:bg-white mt-3">
        <pre className="text-sm whitespace-pre-wrap">{result ? JSON.stringify(result, null, 2) : '—'}</pre>
      </div>
    </div>
  );
}