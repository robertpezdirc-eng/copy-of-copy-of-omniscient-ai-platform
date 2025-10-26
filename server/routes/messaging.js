// server/routes/messaging.js
import express from 'express';
import messaging from '../services/messaging.js';

const router = express.Router();

// Health check for messaging backends
router.get('/health', async (req, res) => {
  try {
    const health = await messaging.health();
    res.json({ success: true, health });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Current messaging config
router.get('/config', (req, res) => {
  res.json({ success: true, config: messaging.config() });
});

// Publish message to Kafka or RabbitMQ
router.post('/publish', async (req, res) => {
  try {
    const { kind, topic, queue, message } = req.body || {};
    if (!kind || (kind !== 'kafka' && kind !== 'rabbit')) {
      return res.status(400).json({ error: 'Specify kind=kafka|rabbit' });
    }
    if (kind === 'kafka' && !topic) {
      return res.status(400).json({ error: 'Missing topic for Kafka' });
    }
    if (kind === 'rabbit' && !queue) {
      return res.status(400).json({ error: 'Missing queue for RabbitMQ' });
    }

    const payload = message ?? { example: 'hello-world', time: new Date().toISOString() };
    const result = kind === 'kafka'
      ? await messaging.publishKafka(topic, payload)
      : await messaging.publishRabbit(queue, payload);

    res.json({ success: result.success, result });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

export default router;