// Simple streaming hook for chat via WebSocket with SSE fallback
// Usage:
// const { stream } = useChatStream({ transport: 'auto' | 'ws' | 'sse' });
// const stop = stream({ prompt, model, provider, temperature, onChunk, onFinal, onEnd, onError });

export function useChatStream({ transport = 'auto' } = {}) {
  const backend = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  function startSSE({ prompt = '', model, provider, temperature, onChunk, onFinal, onEnd, onError }) {
    const url = new URL(backend + '/api/v1/omni-brain/stream');
    url.searchParams.set('prompt', prompt);
    if (model) url.searchParams.set('model', model);
    if (provider) url.searchParams.set('provider', provider);
    if (typeof temperature === 'number') url.searchParams.set('temperature', String(temperature));

    const es = new EventSource(url);

    es.onmessage = (evt) => {
      try {
        const text = evt.data;
        onChunk?.(text);
      } catch (e) {
        onError?.(e);
      }
    };

    es.onerror = (evt) => {
      onError?.(evt);
    };

    const stop = () => {
      es.close();
      // No explicit final in SSE; synthesize final from collected chunks upstream if needed.
      onEnd?.();
    };

    return stop;
  }

  function startWS({ prompt = '', model, provider, temperature, onChunk, onFinal, onEnd, onError, onFallback }) {
    const wsUrl = backend.replace(/^http/, 'ws') + '/api/v1/omni-brain/ws';
    const ws = new WebSocket(wsUrl);
    let gotAnyDelta = false;

    ws.onopen = () => {
      ws.send(
        JSON.stringify({ prompt, model, provider, temperature, options: {} })
      );
    };

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data?.type === 'delta') {
          gotAnyDelta = true;
          onChunk?.(data.data);
        } else if (data?.type === 'final') {
          onFinal?.(data.data);
          ws.close();
        } else if (data?.type === 'error') {
          onError?.(new Error(data.message || 'WS error'));
          // Optionally fallback to SSE upon error
          onFallback?.();
          ws.close();
        } else {
          // Unknown frame; ignore
        }
      } catch (e) {
        // If not JSON (legacy), treat as delta
        gotAnyDelta = true;
        onChunk?.(evt.data);
      }
    };

    ws.onerror = (evt) => {
      onError?.(evt);
      onFallback?.();
    };

    ws.onclose = () => {
      onEnd?.();
    };

    return () => ws.close();
  }

  function stream({ prompt = '', model, provider, temperature, onChunk, onFinal, onEnd, onError }) {
    if (transport === 'sse') {
      return startSSE({ prompt, model, provider, temperature, onChunk, onFinal, onEnd, onError });
    }
    if (transport === 'ws') {
      return startWS({ prompt, model, provider, temperature, onChunk, onFinal, onEnd, onError });
    }

    // auto: try WS first, fallback to SSE
    let stopFunc = () => {};
    let fellBack = false;

    const doFallback = () => {
      if (fellBack) return;
      fellBack = true;
      stopFunc = startSSE({ prompt, model, provider, temperature, onChunk, onFinal, onEnd, onError });
    };

    stopFunc = startWS({ prompt, model, provider, temperature, onChunk, onFinal, onEnd, onError, onFallback: doFallback });

    return () => stopFunc();
  }

  return { stream };
}