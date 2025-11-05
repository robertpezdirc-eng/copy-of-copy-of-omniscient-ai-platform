const { generate } = require('../ollama');
const { timestampUtc } = require('../shared/utils');

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', chunk => { data += chunk; });
    req.on('end', () => {
      try {
        const json = data ? JSON.parse(data) : {};
        resolve(json);
      } catch (e) {
        reject(new Error('Invalid JSON body'));
      }
    });
    req.on('error', reject);
  });
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.statusCode = 405;
    res.setHeader('Allow', 'POST');
    return res.end(JSON.stringify({ ok: false, error: 'Method Not Allowed' }));
  }

  try {
    const body = await readBody(req);
    const model = body.model || process.env.OLLAMA_MODEL || 'llama3';
    const prompt = body.prompt || 'Hello from Omni Enterprise.';
    const options = body.options || {};

    const result = await generate({ model, prompt, options });

    res.statusCode = 200;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ ok: true, timestamp: timestampUtc(), result }));
  } catch (err) {
    res.statusCode = 500;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ ok: false, error: String(err.message || err) }));
  }
};