// server.js
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { askOpenAI } = require('./brainActivity');

const app = express();
const PORT = process.env.PORT || 8082;

// Middleware
app.use(cors());
app.use(express.json());

// Test endpoint za preverjanje povezave
app.get('/api/test', (req, res) => {
    res.json({ status: 'running' });
});

// Endpoint za pošiljanje vprašanj OpenAI
app.post('/api/openai', async (req, res) => {
    const { prompt } = req.body;

    if (!prompt || prompt.trim() === '') {
        return res.status(400).json({ reply: 'Prosimo, vnesite vprašanje.' });
    }

    const answer = await askOpenAI(prompt);
    res.json({ reply: answer });
});

// Zaženi strežnik
app.listen(PORT, () => {
    console.log(`✅ Omni Brain API je zagnan na http://localhost:${PORT}`);
});
