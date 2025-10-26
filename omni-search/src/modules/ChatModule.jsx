import React, { useRef, useState } from 'react';
import { openGeminiStream } from '../sseClient';

export default function ChatModule() {
  const [prompt, setPrompt] = useState('Hello Vertex AI!');
  const [model, setModel] = useState('gemini-2.0-pro');
  const [streamText, setStreamText] = useState('');
  const [status, setStatus] = useState('idle');
  const streamRef = useRef(null);

  const startStream = () => {
    setStatus('streaming');
    setStreamText('');
    if (streamRef.current) streamRef.current.close();
    streamRef.current = openGeminiStream({
      prompt,
      model,
      onChunk: (chunk) => setStreamText((t) => t + chunk),
      onDone: () => setStatus('done'),
      onError: () => setStatus('error'),
    });
  };

  const stopStream = () => {
    if (streamRef.current) {
      try { streamRef.current.close(); } catch {}
      streamRef.current = null;
      setStatus('stopped');
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: 12 }}>AI Chat (SSE streaming)</h2>
      <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Vnesi poziv..."
          rows={3}
          style={{ flex: 1, padding: 8, background: '#0f172a', color: '#e2e8f0', border: '1px solid #1f2937', borderRadius: 6 }}
        />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, width: 220 }}>
          <input
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="Model"
            style={{ padding: 8, background: '#0f172a', color: '#e2e8f0', border: '1px solid #1f2937', borderRadius: 6 }}
          />
          <button onClick={startStream} style={{ padding: 10, borderRadius: 6, background: '#2563eb', color: 'white', border: 0 }}>Start stream</button>
          <button onClick={stopStream} style={{ padding: 10, borderRadius: 6, background: '#ef4444', color: 'white', border: 0 }}>Stop</button>
          <div style={{ fontSize: 12, opacity: 0.8 }}>Status: {status}</div>
        </div>
      </div>
      <div style={{ whiteSpace: 'pre-wrap', background: '#0f172a', color: '#f8fafc', padding: 12, borderRadius: 6, minHeight: 120, border: '1px solid #1f2937' }}>
        {streamText || '—'}
      </div>
    </div>
  );
}