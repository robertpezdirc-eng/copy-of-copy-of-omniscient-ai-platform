const OLLAMA_HOST = process.env.OLLAMA_HOST || 'http://localhost:11434';

async function generate({ model, prompt, options = {} }) {
  const payload = {
    model: model || process.env.OLLAMA_MODEL || 'llama3',
    prompt,
    stream: false,
    ...options,
  };

  const res = await fetch(`${OLLAMA_HOST}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Ollama error ${res.status}: ${text}`);
  }

  const json = await res.json();
  return json;
}

module.exports = {
  generate,
};