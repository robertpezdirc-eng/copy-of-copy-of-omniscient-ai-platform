import { useRef, useState } from 'react';
import { openGeminiStream } from '../sseClient';

export default function GeminiStreamPage() {
  const [prompt, setPrompt] = useState('Pozdravljeni Gemini! Povej nekaj zanimivega.');
  const [model, setModel] = useState('gemini-2.0-pro');
  const [text, setText] = useState('');
  const [status, setStatus] = useState('idle');
  const streamRef = useRef(null);
  const base = process.env.REACT_APP_BACKEND_URL || '';

  const start = () => {
    setStatus('streaming');
    setText('');
    if (streamRef.current) try { streamRef.current.close(); } catch {}
    streamRef.current = openGeminiStream({ baseUrl: base, prompt, model,
      onChunk: (chunk) => setText(t => t + chunk),
      onDone: () => setStatus('done'),
      onError: () => setStatus('error')
    });
  };
  const stop = () => {
    if (streamRef.current) {
      try { streamRef.current.close(); } catch {}
      streamRef.current = null;
      setStatus('stopped');
    }
  };

  return (
    <div className="p-4 text-gray-200 dark:text-gray-900">
      <h2 className="text-2xl font-bold mb-2">Gemini Stream (SSE)</h2>
      <div className="flex gap-2 mb-3">
        <input value={prompt} onChange={e=>setPrompt(e.target.value)} className="flex-1 px-3 py-2 rounded bg-gray-900 text-white border border-gray-700 dark:bg-white dark:text-black dark:border-gray-300" />
        <input value={model} onChange={e=>setModel(e.target.value)} className="w-48 px-3 py-2 rounded bg-gray-900 text-white border border-gray-700 dark:bg-white dark:text-black dark:border-gray-300" />
        <button onClick={start} className="px-3 py-2 rounded bg-blue-600 text-white">Start</button>
        <button onClick={stop} className="px-3 py-2 rounded bg-red-600 text-white">Stop</button>
        <span className="text-xs font-mono">Status: {status}</span>
      </div>
      <div className="p-3 rounded-lg border border-gray-800 bg-black/30 dark:bg-white">
        <pre className="text-sm whitespace-pre-wrap">{text || '—'}</pre>
      </div>
    </div>
  );
}