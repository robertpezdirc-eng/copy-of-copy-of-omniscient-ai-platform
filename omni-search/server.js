/**
 * 🌐 OMNI AI Integration Server
 * Povezuje ChatGPT, Gemini in OMNI Director za funkcionalno spletno platformo
 */

import express from 'express';
import cors from 'cors';
import axios from 'axios';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

// Load environment variables from .env file
console.log('🔧 Loading environment variables...');
console.log(`🔧 Current directory: ${process.cwd()}`);
const envPath = path.join(process.cwd(), '.env');
console.log(`🔧 .env file path: ${envPath}`);
console.log(`🔧 .env file exists: ${fs.existsSync('.env')}`);
if (fs.existsSync('.env')) {
  const envContent = fs.readFileSync('.env', 'utf8');
  console.log(`🔧 .env file content preview: ${envContent.split('\n')[4]?.substring(0, 30) + '...'}`);
  const result = dotenv.config({ path: envPath, override: true });
  if (result.error) {
    console.error('🔧 Error loading .env file:', result.error);
  }
  console.log(`🔧 OPENAI_API_KEY loaded: ${process.env.OPENAI_API_KEY ? process.env.OPENAI_API_KEY.substring(0, 20) + '...' : 'Not loaded'}`);
} else {
  console.log('🔧 .env file not found, using system environment variables');
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3001;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'dist')));

// AI API konfiguracija
const AI_PROVIDERS = {
    openai: {
        baseURL: 'https://api.openai.com/v1',
        model: 'gpt-4',
        requiresAuth: true
    },
    gemini: {
        baseURL: 'https://generativelanguage.googleapis.com/v1',
        model: 'gemini-pro',
        requiresAuth: true
    },
    omni: {
        baseURL: 'local',
        model: 'omni-director',
        requiresAuth: false
    }
};

// API key validation functions
const validateApiKey = (key, provider) => {
    if (!key || typeof key !== 'string') {
        return { isValid: false, reason: 'API key is missing or not a string' };
    }

    const trimmedKey = key.trim();

    switch (provider) {
        case 'openai':
            console.log(`🔍 Validating OpenAI key: ${trimmedKey.substring(0, 20)}...`);
            const startsSk = trimmedKey.startsWith('sk-');
            const startsSkProj = trimmedKey.startsWith('sk-proj-');
            console.log(`🔍 Key starts with sk-: ${startsSk}`);
            console.log(`🔍 Key starts with sk-proj-: ${startsSkProj}`);
            console.log(`🔍 Key length: ${trimmedKey.length}`);

            if (!(startsSk || startsSkProj)) {
                return { isValid: false, reason: 'OpenAI API key must start with sk- or sk-proj-' };
            }
            if (trimmedKey.length < 40) {
                return { isValid: false, reason: 'OpenAI API key is too short' };
            }
            break;
        case 'gemini':
            if (trimmedKey.length < 30) {
                return { isValid: false, reason: 'Gemini API key is too short' };
            }
            break;
        default:
            return { isValid: false, reason: 'Unknown provider' };
    }

    return { isValid: true, cleanKey: trimmedKey };
};

// Environment variable validation and API key management
const validateEnvironmentVariables = () => {
    const required = [];
    const optional = ['OPENAI_API_KEY', 'GEMINI_API_KEY'];

    console.log('🔧 Validating environment variables...');

    const results = {
        openai: { configured: false, valid: false },
        gemini: { configured: false, valid: false }
    };

    // Check OpenAI API key
    if (process.env.OPENAI_API_KEY) {
        results.openai.configured = true;
        const validation = validateApiKey(process.env.OPENAI_API_KEY, 'openai');
        results.openai.valid = validation.isValid;

        if (!validation.isValid) {
            console.warn(`⚠️ OPENAI_API_KEY: ${validation.reason}`);
        } else {
            console.log('✅ OPENAI_API_KEY: Valid format');
        }
    } else {
        console.log('⚠️ OPENAI_API_KEY: Not configured (will fallback to OMNI)');
    }

    // Check Gemini API key
    if (process.env.GEMINI_API_KEY) {
        results.gemini.configured = true;
        const validation = validateApiKey(process.env.GEMINI_API_KEY, 'gemini');
        results.gemini.valid = validation.isValid;

        if (!validation.isValid) {
            console.warn(`⚠️ GEMINI_API_KEY: ${validation.reason}`);
        } else {
            console.log('✅ GEMINI_API_KEY: Valid format');
        }
    } else {
        console.log('⚠️ GEMINI_API_KEY: Not configured (will fallback to OMNI)');
    }

    return results;
};

// API key management (use environment variables in production)
let apiKeys = {
    openai: process.env.OPENAI_API_KEY || null,
    gemini: process.env.GEMINI_API_KEY || null
};

// Validate environment on startup
const envValidation = validateEnvironmentVariables();


// OMNI Director - koordinira med AI storitvami
class OmniDirector {
    constructor() {
        this.aiProviders = new Map();
        this.conversationHistory = new Map();
        this.systemPrompt = `Ti si OMNI Director, napredni AI koordinator ki upravlja več AI storitev.
        Naloga: Inteligentno usmerjaj uporabnikova vprašanja na najprimernejšo AI storitev.
        - Za kreativno pisanje in kode: uporabi ChatGPT
        - Za analitična vprašanja in raziskave: uporabi Gemini
        - Za sistemsko upravljanje: uporabi OMNI funkcije
        Vedno odgovarjaj v slovenščini in bodi pomočen.`;
    }

    async processQuery(query, userId = 'default', preferredAI = 'auto') {
        const conversationId = `${userId}_${Date.now()}`;

        try {
            // Analiziraj query in določi najboljšo AI storitev
            const selectedAI = this.selectBestAI(query, preferredAI);

            console.log(`🎯 Selected AI: ${selectedAI} for query: ${query.substring(0, 50)}...`);

            // Izvedi query na izbrani AI storitvi
            const response = await this.callAIProvider(selectedAI, query, conversationId);

            // Shrani v zgodovino
            this.saveToHistory(conversationId, query, response, selectedAI);

            return {
                success: true,
                response: response,
                usedAI: selectedAI,
                conversationId: conversationId,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            console.error('❌ Error in OMNI Director:', error);

            // Handle specific error types
            let errorMessage = "Oprostite, prišlo je do napake pri procesiranju vašega vprašanja.";
            let errorCode = "INTERNAL_ERROR";

            if (error.message === 'OPENAI_API_KEY_INVALID') {
                errorMessage = "OpenAI API ključ ni pravilno konfiguriran. Uporabljam OMNI AI.";
                errorCode = "API_KEY_INVALID";
            } else if (error.message.includes('timeout')) {
                errorMessage = "Zahteva je trajala predolgo. Poskusite znova.";
                errorCode = "TIMEOUT";
            } else if (error.message.includes('network') || error.message.includes('ECONNREFUSED')) {
                errorMessage = "Težava z omrežno povezavo. Poskusite znova.";
                errorCode = "NETWORK_ERROR";
            }

            return {
                success: false,
                error: errorCode,
                message: errorMessage,
                fallback: "OMNI AI je vedno na voljo kot alternativa."
            };
        }
    }

    selectBestAI(query, preferredAI) {
        if (preferredAI !== 'auto') {
            // Preveri če je zahtevani provider dosegljiv
            if (preferredAI === 'openai' && !apiKeys.openai) {
                console.log('⚠️ OpenAI requested but not configured, using OMNI');
                return 'omni';
            }
            if (preferredAI === 'gemini' && !apiKeys.gemini) {
                console.log('⚠️ Gemini requested but not configured, using OMNI');
                return 'omni';
            }
            return preferredAI;
        }

        const lowerQuery = query.toLowerCase();

        // Preveri katere AI storitve so dosegljive
        const availableProviders = [];
        if (apiKeys.openai) availableProviders.push('openai');
        if (apiKeys.gemini) availableProviders.push('gemini');
        availableProviders.push('omni'); // OMNI je vedno dosegljiv

        // Analiza query-ja za določitev najboljše AI storitve
        if (lowerQuery.includes('koda') || lowerQuery.includes('program') || lowerQuery.includes('code') ||
            lowerQuery.includes('napiši') || lowerQuery.includes('ustvari') || lowerQuery.includes('generate')) {
            return availableProviders.includes('openai') ? 'openai' : 'omni';
        }

        if (lowerQuery.includes('analiz') || lowerQuery.includes('razisk') || lowerQuery.includes('research') ||
            lowerQuery.includes('podatki') || lowerQuery.includes('statistik') || lowerQuery.includes('data')) {
            return availableProviders.includes('gemini') ? 'gemini' :
                   (availableProviders.includes('openai') ? 'openai' : 'omni');
        }

        if (lowerQuery.includes('omni') || lowerQuery.includes('sistem') || lowerQuery.includes('system') ||
            lowerQuery.includes('agent') || lowerQuery.includes('koordin')) {
            return 'omni'; // OMNI za sistemske zadeve
        }

        // Privzeto uporabi OMNI če nobena zunanja storitev ni konfigurirana
        if (availableProviders.length === 1 && availableProviders[0] === 'omni') {
            return 'omni';
        }

        // Če so zunanje storitve dosegljive, uporabi najboljšo
        if (availableProviders.includes('openai')) return 'openai';
        if (availableProviders.includes('gemini')) return 'gemini';
        return 'omni';
    }

    async callAIProvider(provider, query, conversationId) {
        switch (provider) {
            case 'openai':
                return await this.callOpenAI(query, conversationId);
            case 'gemini':
                return await this.callGemini(query, conversationId);
            case 'omni':
                return await this.callOmniAI(query, conversationId);
            default:
                throw new Error(`Unknown AI provider: ${provider}`);
        }
    }

    async callOpenAI(query, conversationId) {
        if (!apiKeys.openai) {
            throw new Error('OpenAI API key not configured');
        }

        // Clean the API key (be more lenient)
        const cleanApiKey = apiKeys.openai.trim();

        // Validate API key using the centralized validation function
        const validation = validateApiKey(cleanApiKey, 'openai');

        if (!validation.isValid) {
            console.log(`⚠️ OpenAI API key validation failed: ${validation.reason}`);
            console.log('🔄 Falling back to OMNI AI provider');
            throw new Error('OPENAI_API_KEY_INVALID');
        }

        console.log('✅ OpenAI API key validated successfully');

        const response = await axios.post('https://api.openai.com/v1/chat/completions', {
            model: 'gpt-4',
            messages: [
                { role: 'system', content: this.systemPrompt },
                { role: 'user', content: query }
            ],
            max_tokens: 1000,
            temperature: 0.7
        }, {
            headers: {
                'Authorization': `Bearer ${cleanApiKey}`,
                'Content-Type': 'application/json'
            },
            timeout: 30000
        });

        return response.data.choices[0].message.content;
    }

    async callGemini(query, conversationId) {
        if (!apiKeys.gemini) {
            throw new Error('Gemini API key not configured');
        }

        // Clean the Gemini API key
        const cleanGeminiKey = apiKeys.gemini.trim();

        const response = await axios.post(`https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=${cleanGeminiKey}`, {
            contents: [{
                parts: [{
                    text: `${this.systemPrompt}\n\nUser: ${query}`
                }]
            }],
            generationConfig: {
                temperature: 0.7,
                maxOutputTokens: 1000
            }
        }, {
            timeout: 30000
        });

        return response.data.candidates[0].content.parts[0].text;
    }

    async callOmniAI(query, conversationId) {
        // OMNI AI - lokalna funkcionalnost z inteligentnimi odgovori
        const lowerQuery = query.toLowerCase();

        if (lowerQuery.includes('status') || lowerQuery.includes('stanje')) {
            return `🟢 OMNI Sistem Status:
• Aktivni agenti: 8/8
• API povezave: Delujoče
• Sistemsko zdravje: 98%
• Lokacija: Standalone način
• Učenje v ozadju: Aktivno
• ChatGPT: ${apiKeys.openai ? 'Povezan' : 'Ni konfiguriran'}
• Gemini: ${apiKeys.gemini ? 'Povezan' : 'Ni konfiguriran'}`;

        } else if (lowerQuery.includes('agenti') || lowerQuery.includes('agents')) {
            return `🤖 Aktivni OMNI Agenti:
• 👑 Omni Director: Glavni koordinator (JAZ)
• 📊 Data Analyzer: Analiza podatkov v realnem času
• 🤖 Omni Chat: AI asistent za uporabnike
• 👁️ Vision Core: Procesiranje slik in objektov
• 💳 Omni Billing: Upravljanje naročnin in plačil
• ⚡ AI Generator: Ustvarjanje besedil, slik in kode
• 🛡️ Security Sentinel: Varnostni nadzor in protokoli
• 💻 Kilo Code: Generator programske kode

Vsi agenti so povezani in delujejo v slovenskem jeziku.`;

        } else if (lowerQuery.includes('pomoč') || lowerQuery.includes('help')) {
            return `💡 OMNI Pomoč:
• Vprašajte me karkoli v slovenščini
• Uporabljam ChatGPT za ustvarjanje in kodiranje
• Uporabljam Gemini za analize in raziskave
• Koordiniram med vsemi AI storitvami
• Delujem 24/7 v slovenskem jeziku
• Učenje agentov poteka v ozadju

💬 Preizkusite: "Kako deluje umetna inteligenca?"`;

        } else if (lowerQuery.includes('zdravo') || lowerQuery.includes('pozdrav') || lowerQuery.includes('hi') || lowerQuery.includes('hello')) {
            return `👋 Pozdravljeni! Sem OMNI Director, vaš slovenski AI asistent.

Tukaj sem da vam pomagam z:
• 🔍 Iskanjem informacij
• 🤖 Upravljanjem z OMNI agenti
• 📚 Učenjem in izboljševanjem
• 💬 Pogovorom v slovenščini

Kako vam lahko pomagam danes?`;

        } else if (lowerQuery.includes('kako') || lowerQuery.includes('zakaj') || lowerQuery.includes('kje')) {
            return `🤔 Kot OMNI Director analiziram vaše vprašanje: "${query}"

Glede na vašo poizvedbo vam priporočam:
• Če potrebujete hitre odgovore → uporabite ChatGPT
• Če potrebujete analize → uporabite Gemini
• Če potrebujete sistemske informacije → ostanite z mano

Želite da vas povežem z drugo AI storitvijo?`;

        } else {
            // Inteligenten odgovor glede na kontekst
            const responses = [
                `🤖 Kot OMNI Director sem procesiral vaše vprašanje: "${query}"

To je zanimiva tema! Če želite podrobnejšo analizo, vas lahko povežem z:
• ChatGPT za kreativne odgovore
• Gemini za raziskovalne odgovore
• OMNI AI za sistemske informacije`,

                `💡 Analiziral sem vašo poizvedbo in kot slovenski AI asistent vam podajam ta odgovor.

Če potrebujete več informacij, mi lahko postavite nadaljnja vprašanja ali vas povežem z specializirano AI storitvijo.`,

                `🌟 OMNI odgovor: Razumel sem vaše vprašanje o "${query}".

Kot napredni AI koordinator vam zagotavljam natančne in relevantne odgovore. Če želite poglobljeno analizo, priporočam ChatGPT ali Gemini.`
            ];

            return responses[Math.floor(Math.random() * responses.length)];
        }
    }

    saveToHistory(conversationId, query, response, aiProvider) {
        this.conversationHistory.set(conversationId, {
            query,
            response,
            aiProvider,
            timestamp: new Date()
        });

        // Ohrani samo zadnjih 100 pogovorov
        if (this.conversationHistory.size > 100) {
            const firstKey = this.conversationHistory.keys().next().value;
            this.conversationHistory.delete(firstKey);
        }
    }

    getConversationHistory(userId) {
        const userConversations = [];
        for (const [id, data] of this.conversationHistory) {
            if (id.startsWith(userId)) {
                userConversations.push({ id, ...data });
            }
        }
        return userConversations.reverse();
    }
}

// Inicializiraj OMNI Director
const omniDirector = new OmniDirector();

// API Endpoints

// Status endpoint
app.get('/api/agents/status', (req, res) => {
    res.json({
        status: 'online',
        agents: 8,
        providers: {
            openai: !!apiKeys.openai,
            gemini: !!apiKeys.gemini,
            omni: true
        },
        timestamp: new Date().toISOString()
    });
});

// Chat endpoint - glavni endpoint za vse AI storitve
app.post('/api/chat', async (req, res) => {
    try {
        const { message, userId = 'default', aiProvider = 'auto' } = req.body;

        if (!message) {
            return res.status(400).json({
                success: false,
                error: 'Message is required'
            });
        }

        console.log(`💬 Processing chat: ${message.substring(0, 50)}...`);

        const result = await omniDirector.processQuery(message, userId, aiProvider);

        res.json(result);

    } catch (error) {
        console.error('❌ Chat API Error:', error);

        let errorMessage = 'Notranja napaka strežnika';
        let statusCode = 500;
        let errorCode = 'INTERNAL_ERROR';
        let suggestion = 'Poskusite znova ali uporabite OMNI AI kot alternativo.';

        // Handle specific error types with appropriate status codes and messages
        if (error.message === 'OPENAI_API_KEY_INVALID') {
            errorMessage = 'OpenAI API ključ ni veljaven ali ni pravilno konfiguriran.';
            statusCode = 400;
            errorCode = 'INVALID_API_KEY';
            suggestion = 'Preverite OPENAI_API_KEY environment variable ali uporabite OMNI AI.';
        } else if (error.message.includes('API key not configured')) {
            errorMessage = 'AI API ključ ni konfiguriran.';
            statusCode = 400;
            errorCode = 'API_KEY_MISSING';
            suggestion = 'Nastavite OPENAI_API_KEY environment variable.';
        } else if (error.message.includes('timeout') || error.code === 'ECONNABORTED') {
            errorMessage = 'Zahteva je trajala predolgo.';
            statusCode = 408;
            errorCode = 'TIMEOUT';
            suggestion = 'Poskusite znova ali uporabite OMNI AI za hitrejši odziv.';
        } else if (error.message.includes('network') || error.message.includes('ECONNREFUSED')) {
            errorMessage = 'Težava z omrežno povezavo do AI storitve.';
            statusCode = 502;
            errorCode = 'NETWORK_ERROR';
            suggestion = 'Preverite internetno povezavo ali uporabite OMNI AI.';
        } else if (error.message.includes('Invalid character')) {
            errorMessage = 'API ključ vsebuje neveljavne znake.';
            statusCode = 400;
            errorCode = 'INVALID_API_KEY_FORMAT';
            suggestion = 'Preverite format OPENAI_API_KEY - mora se začeti z "sk-" ali "sk-proj-".';
        }

        res.status(statusCode).json({
            success: false,
            error: errorCode,
            message: errorMessage,
            suggestion: suggestion,
            timestamp: new Date().toISOString()
        });
    }
});

// Direct OpenAI endpoint
app.post('/api/chat/openai', async (req, res) => {
    try {
        const { message } = req.body;

        if (!message) {
            return res.status(400).json({ error: 'Message required' });
        }

        if (!apiKeys.openai) {
            return res.status(400).json({ error: 'OpenAI API key not configured' });
        }

        const response = await axios.post('https://api.openai.com/v1/chat/completions', {
            model: 'gpt-4',
            messages: [{ role: 'user', content: message }],
            max_tokens: 1000,
            temperature: 0.7
        }, {
            headers: {
                'Authorization': `Bearer ${apiKeys.openai}`,
                'Content-Type': 'application/json'
            }
        });

        res.json({
            success: true,
            response: response.data.choices[0].message.content,
            provider: 'openai'
        });

    } catch (error) {
        console.error('❌ OpenAI API Error:', error);
        res.status(500).json({
            success: false,
            error: 'OpenAI API error',
            message: error.message
        });
    }
});

// Direct Gemini endpoint
app.post('/api/chat/gemini', async (req, res) => {
    try {
        const { message } = req.body;

        if (!message) {
            return res.status(400).json({ error: 'Message required' });
        }

        if (!apiKeys.gemini) {
            return res.status(400).json({ error: 'Gemini API key not configured' });
        }

        const response = await axios.post(`https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=${apiKeys.gemini}`, {
            contents: [{
                parts: [{ text: message }]
            }]
        });

        res.json({
            success: true,
            response: response.data.candidates[0].content.parts[0].text,
            provider: 'gemini'
        });

    } catch (error) {
        console.error('❌ Gemini API Error:', error);
        res.status(500).json({
            success: false,
            error: 'Gemini API error',
            message: error.message
        });
    }
});

// API key management
app.post('/api/admin/keys', (req, res) => {
    const { openai, gemini } = req.body;

    if (openai) apiKeys.openai = openai;
    if (gemini) apiKeys.gemini = gemini;

    res.json({
        success: true,
        configured: {
            openai: !!apiKeys.openai,
            gemini: !!apiKeys.gemini
        }
    });
});

// Conversation history
app.get('/api/history/:userId', (req, res) => {
    const history = omniDirector.getConversationHistory(req.params.userId);
    res.json({ success: true, history });
});

// Health check
app.get('/api/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        version: '1.0.0'
    });
});

// OMNI Learning Overlay endpoints
app.get('/api/learning/status', (req, res) => {
    try {

        const memoryPath = path.join(__dirname, '..', 'omni_learning_overlay', 'memory');
        const configPath = path.join(__dirname, '..', 'omni_learning_overlay', 'overlay_config.json');

        let agentsMemory = {};
        let totalTopics = 0;

        // Preberi spomin agentov
        if (fs && fs.existsSync && fs.existsSync(memoryPath)) {
            const files = fs.readdirSync(memoryPath);
            files.forEach(file => {
                if (file.endsWith('.json')) {
                    const agentId = file.replace('.json', '');
                    const filePath = path.join(memoryPath, file);

                    try {
                        const memory = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                        agentsMemory[agentId] = {
                            topics_learned: memory.length,
                            latest_topic: memory.length > 0 ? memory[memory.length - 1].topic : null,
                            last_updated: memory.length > 0 ? memory[memory.length - 1].timestamp : null
                        };
                        totalTopics += memory.length;
                    } catch (e) {
                        console.error(`Error reading memory file ${file}:`, e);
                    }
                }
            });
        }

        res.json({
            success: true,
            learning_overlay: {
                active: true,
                total_agents_learning: Object.keys(agentsMemory).length,
                total_topics_learned: totalTopics,
                agents_memory: agentsMemory,
                last_updated: new Date().toISOString()
            }
        });

    } catch (error) {
        console.error('Error getting learning status:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to get learning status',
            message: error.message
        });
    }
});

app.get('/api/learning/analytics', (req, res) => {
    try {
        const fs = require('fs');
        const path = require('path');

        const memoryPath = path.join(__dirname, '..', 'omni_learning_overlay', 'memory');

        if (!fs || !fs.existsSync || !fs.existsSync(memoryPath)) {
            return res.json({
                success: true,
                analytics: {
                    total_agents: 0,
                    total_topics: 0,
                    agents: {}
                }
            });
        }

        const files = fs.readdirSync(memoryPath);
        let agents = {};
        let totalTopics = 0;

        files.forEach(file => {
            if (file.endsWith('.json')) {
                const agentId = file.replace('.json', '');
                const filePath = path.join(memoryPath, file);

                try {
                    const memory = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                    agents[agentId] = {
                        topics_learned: memory.length,
                        latest_topic: memory.length > 0 ? memory[memory.length - 1].topic : null,
                        memory_size: JSON.stringify(memory).length
                    };
                    totalTopics += memory.length;
                } catch (e) {
                    console.error(`Error reading memory file ${file}:`, e);
                }
            }
        });

        res.json({
            success: true,
            analytics: {
                total_agents: Object.keys(agents).length,
                total_topics: totalTopics,
                agents: agents,
                generated_at: new Date().toISOString()
            }
        });

    } catch (error) {
        console.error('Error getting learning analytics:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to get learning analytics',
            message: error.message
        });
    }
});

// Additional APIs: Platform Status, Gemini SSE Stream, Modules Invoke
app.get('/api/platform/status', (req, res) => {
  try {
    const now = new Date();
    const payload = {
      status: 'healthy',
      system_health: 97,
      agents: 8,
      modules: 15,
      active_connections: 3,
      timestamp: now.toISOString(),
    };
    res.json(payload);
  } catch (e) {
    res.status(500).json({ status: 'error', error: e.message });
  }
});

// Simple SSE stream for Gemini demo. If real Gemini is needed, integrate Vertex AI SDK.
app.get('/api/gcp/gemini/stream', async (req, res) => {
  const prompt = String(req.query.prompt || 'Hello from OMNI SSE');
  const model = String(req.query.model || 'gemini-2.0-pro');

  res.set({
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no'
  });
  res.flushHeaders?.();

  const send = (event, data) => {
    if (event) res.write(`event: ${event}\n`);
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };

  try {
    send(null, { chunk: `Model: ${model}\n` });
    send(null, { chunk: `Prompt: ${prompt}\n` });
    let i = 0;
    const chunks = [
      'Streaming odgovor 1...\n',
      'Streaming odgovor 2...\n',
      'Streaming odgovor 3...\n'
    ];
    const interval = setInterval(() => {
      if (i < chunks.length) {
        send(null, { chunk: chunks[i] });
        i++;
      } else {
        clearInterval(interval);
        send('done', { ok: true, model, bytes: prompt.length });
        try { res.end(); } catch {}
      }
    }, 500);
  } catch (e) {
    send('error', { ok: false, error: e.message });
    try { res.end(); } catch {}
  }
});

// Generic module invocation endpoint
app.post('/api/modules/invoke', async (req, res) => {
  const { module, action, params } = req.body || {};
  if (!module || !action) {
    return res.status(400).json({ ok: false, error: 'module and action required' });
  }
  try {
    // TODO: route to actual module implementations
    res.json({ ok: true, module, action, params: params || {}, result: `Invoked ${module}.${action}` });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// Serve React app for all other routes (handle both dev and prod)
app.use((req, res) => {
    // In development, serve the React dev server
    // In production, serve from dist
    const indexPath = path.join(__dirname, 'dist', 'index.html');

    if (fs.existsSync(indexPath)) {
        res.sendFile(indexPath);
    } else {
        // Development fallback
        res.send(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>OMNI Search - Development Mode</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(45deg, #1a1a2e, #16213e);
                        color: white;
                        text-align: center;
                    }
                </style>
            </head>
            <body>
                <div>
                    <h1>🌐 OMNI Search</h1>
                    <p>React development server should be running on port 8080</p>
                    <p>API server is running on port 3001</p>
                    <p><a href="http://localhost:8080" style="color: #0ff;">Open Frontend</a></p>
                </div>
            </body>
            </html>
        `);
    }
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 OMNI AI Integration Server running on port ${PORT}`);
    console.log(`🌐 Frontend: http://localhost:8080`);
    console.log(`🔗 API Base: http://localhost:${PORT}/api`);
    console.log(`🤖 Available providers: OpenAI, Gemini, OMNI Director`);

    // Enhanced API keys status with validation results
    console.log(`🔑 API Keys Status:`);
    console.log(`   OpenAI: ${envValidation.openai.configured ?
        (envValidation.openai.valid ? '✅ Configured & Valid' : '⚠️ Configured but Invalid') :
        '❌ Not configured'}`);
    console.log(`   Gemini: ${envValidation.gemini.configured ?
        (envValidation.gemini.valid ? '✅ Configured & Valid' : '⚠️ Configured but Invalid') :
        '❌ Not configured'}`);
    console.log(`   OMNI: ✅ Built-in (Always available)`);

    if (!envValidation.openai.valid && envValidation.openai.configured) {
        console.log(`\n💡 To fix OpenAI API key issues:`);
        console.log(`   - Ensure OPENAI_API_KEY starts with 'sk-' or 'sk-proj-'`);
        console.log(`   - Verify the key length is at least 50 characters`);
        console.log(`   - Check for any special characters that might cause issues`);
    }
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('🛑 Shutting down OMNI server...');
    process.exit(0);
});

// Export for ES modules
export default app;