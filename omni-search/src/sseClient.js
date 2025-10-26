// Simple EventSource client for Gemini stream
export function openGeminiStream({ baseUrl, prompt, model, onChunk, onDone, onError }) {
  const backend = baseUrl || process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';
  const url = new URL('/api/gcp/gemini/stream', backend);
  url.searchParams.set('prompt', prompt || '');
  if (model) url.searchParams.set('model', model);

  const es = new EventSource(url.toString(), { withCredentials: false });

  es.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data);
      if (data?.chunk) onChunk?.(data.chunk, data);
    } catch (e) {
      // ignore parse errors
    }
  };

  es.addEventListener('done', (ev) => {
    try {
      const data = JSON.parse(ev.data);
      onDone?.(data);
    } catch (e) {
      onDone?.({ ok: true });
    }
    es.close();
  });

  es.onerror = (err) => {
    onError?.(err);
    try { es.close(); } catch {}
  };

  return es;
}