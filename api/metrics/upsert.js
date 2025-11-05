module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.statusCode = 405;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ ok: false, error: 'Method Not Allowed' }));
    return;
  }

  try {
    const chunks = [];
    for await (const chunk of req) {
      chunks.push(chunk);
    }
    const bodyString = Buffer.concat(chunks).toString();
    let payload = {};
    try {
      payload = bodyString ? JSON.parse(bodyString) : {};
    } catch (e) {
      payload = { raw: bodyString };
    }

    const moduleName = payload.module || 'unknown';
    const entry = payload.entry || {};

    res.statusCode = 200;
    res.setHeader('Content-Type', 'application/json');
    res.end(
      JSON.stringify({
        ok: true,
        status: 'upserted',
        module: moduleName,
        entry,
        source: 'api/metrics/upsert',
        timestamp: new Date().toISOString(),
      })
    );
  } catch (err) {
    res.statusCode = 500;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ ok: false, error: err.message }));
  }
};