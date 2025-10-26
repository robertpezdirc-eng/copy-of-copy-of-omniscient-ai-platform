// Simple OAuth and HAL microservice with VR Integration
const express = require('express');
const morgan = require('morgan');
const cors = require('cors');

// Mock HAL
const HAL = require('./modules/hw-hal');

// VR Core Integration - JavaScript version
class OmniVRCoreJS {
    constructor() {
        this.devices = new Map();
        this.sessions = new Map();
        this.projects = new Map();
        this.websocketClients = new Map();

        // VR Configuration
        this.config = {
            maxDevices: 100,
            maxSessionsPerDevice: 5,
            sessionTimeout: 3600000, // milliseconds
            heartbeatInterval: 30000, // milliseconds
            supportedFrameworks: ["aframe", "three.js", "babylon.js"],
            autoCleanup: true,
            enableQuantumIntegration: true,
            enableAiAssistance: true
        };

        // Load existing projects
        this.loadVRProjects();

        // Start background services
        this.startBackgroundServices();

        console.log('🎮 OMNI VR Core (JS) initialized successfully');
    }

    loadVRProjects() {
        try {
            // Load project metadata from vr_gateway.json
            const fs = require('fs');
            const path = require('path');

            const gatewayConfigPath = path.join(__dirname, 'vr_gateway.json');
            if (fs.existsSync(gatewayConfigPath)) {
                const config = JSON.parse(fs.readFileSync(gatewayConfigPath, 'utf8'));

                // Load example projects
                const examples = config.examples || {};
                for (const [projectKey, projectData] of Object.entries(examples)) {
                    const project = {
                        projectId: `example_${projectKey}`,
                        name: projectData.name,
                        description: projectData.description,
                        framework: projectData.framework,
                        projectType: "example",
                        createdAt: new Date(),
                        createdBy: "system",
                        filePath: `vr_projects/templates/${projectData.framework}_basic.html`,
                        status: "ready",
                        accessCount: 0
                    };
                    this.projects.set(project.projectId, project);
                }
            }

            console.log(`✅ Loaded ${this.projects.size} VR projects`);
        } catch (error) {
            console.error('⚠️ Failed to load VR projects:', error.message);
        }
    }

    startBackgroundServices() {
        // Device heartbeat monitor
        setInterval(() => {
            this.deviceHeartbeatMonitor();
        }, this.config.heartbeatInterval);

        // Session cleanup
        setInterval(() => {
            this.sessionCleanup();
        }, 60000); // Check every minute

        console.log('🎮 VR background services started');
    }

    registerVRDevice(deviceInfo, userId) {
        try {
            const deviceId = this.generateId();

            // Determine device type
            const deviceTypeStr = deviceInfo.deviceType || 'other';
            let deviceType = 'other';

            if (deviceTypeStr.toLowerCase().includes('oculus')) deviceType = 'oculus_quest';
            else if (deviceTypeStr.toLowerCase().includes('vive')) deviceType = 'htc_vive';
            else if (deviceTypeStr.toLowerCase().includes('mobile')) deviceType = 'mobile_vr';
            else if (deviceTypeStr.toLowerCase().includes('desktop')) deviceType = 'desktop_vr';

            const device = {
                deviceId,
                deviceType,
                deviceName: deviceInfo.deviceName || `VR Device ${deviceId.substring(0, 8)}`,
                userId,
                connectedAt: new Date(),
                lastSeen: new Date(),
                capabilities: deviceInfo.capabilities || {},
                status: "connected"
            };

            this.devices.set(deviceId, device);

            console.log(`🎮 VR Device registered: ${device.deviceName} (${deviceType})`);
            return deviceId;

        } catch (error) {
            console.error('❌ Failed to register VR device:', error.message);
            return null;
        }
    }

    createVRSession(deviceId, projectId, userId) {
        try {
            if (!this.devices.has(deviceId)) {
                return null;
            }

            const sessionId = this.generateId();

            // Get project info
            const project = this.projects.get(projectId);
            if (!project) {
                return null;
            }

            const session = {
                sessionId,
                deviceId,
                userId,
                projectId,
                framework: project.framework,
                startedAt: new Date(),
                status: "active",
                metrics: {}
            };

            this.sessions.set(sessionId, session);

            // Update device last seen
            const device = this.devices.get(deviceId);
            if (device) {
                device.lastSeen = new Date();
            }

            // Update project access count
            project.accessCount++;

            console.log(`🎮 VR Session created: ${sessionId} for project ${project.name}`);
            return sessionId;

        } catch (error) {
            console.error('❌ Failed to create VR session:', error.message);
            return null;
        }
    }

    endVRSession(sessionId) {
        try {
            const session = this.sessions.get(sessionId);
            if (session) {
                session.status = "ended";

                // Update device last seen
                const device = this.devices.get(session.deviceId);
                if (device) {
                    device.lastSeen = new Date();
                }

                console.log(`🎮 VR Session ended: ${sessionId}`);
                return true;
            }
            return false;

        } catch (error) {
            console.error('❌ Failed to end VR session:', error.message);
            return false;
        }
    }

    getVRDeviceStatus(deviceId) {
        const device = this.devices.get(deviceId);
        if (!device) {
            return { error: "Device not found" };
        }

        return {
            deviceId: device.deviceId,
            deviceName: device.deviceName,
            deviceType: device.deviceType,
            status: device.status,
            connectedAt: device.connectedAt.toISOString(),
            lastSeen: device.lastSeen.toISOString(),
            capabilities: device.capabilities,
            activeSessions: Array.from(this.sessions.values())
                .filter(session => session.deviceId === deviceId && session.status === "active")
                .map(session => session.sessionId)
        };
    }

    getVRProjectsList() {
        return Array.from(this.projects.values()).map(project => ({
            projectId: project.projectId,
            name: project.name,
            description: project.description,
            framework: project.framework,
            projectType: project.projectType,
            createdAt: project.createdAt.toISOString(),
            accessCount: project.accessCount,
            status: project.status
        }));
    }

    getVRSessionInfo(sessionId) {
        const session = this.sessions.get(sessionId);
        if (!session) {
            return { error: "Session not found" };
        }

        const device = this.devices.get(session.deviceId);
        const project = this.projects.get(session.projectId);

        return {
            sessionId: session.sessionId,
            deviceName: device ? device.deviceName : "Unknown",
            projectName: project ? project.name : "Unknown",
            framework: session.framework,
            startedAt: session.startedAt.toISOString(),
            status: session.status,
            metrics: session.metrics
        };
    }

    deviceHeartbeatMonitor() {
        try {
            const currentTime = new Date();
            const inactiveDevices = [];

            for (const [deviceId, device] of this.devices) {
                // Check if device hasn't been seen for too long
                if ((currentTime - device.lastSeen) > 300000) { // 5 minutes
                    device.status = "inactive";
                    inactiveDevices.push(deviceId);
                }
            }

            // Remove very old inactive devices
            for (const deviceId of inactiveDevices) {
                if ((currentTime - this.devices.get(deviceId).lastSeen) > 1800000) { // 30 minutes
                    this.devices.delete(deviceId);
                    console.log(`🗑️ Removed inactive VR device: ${deviceId}`);
                }
            }

        } catch (error) {
            console.error('⚠️ Device heartbeat monitor error:', error.message);
        }
    }

    sessionCleanup() {
        try {
            const currentTime = new Date();
            const expiredSessions = [];

            for (const [sessionId, session] of this.sessions) {
                if (session.status === "active") {
                    // Check if session has expired
                    if ((currentTime - session.startedAt) > this.config.sessionTimeout) {
                        session.status = "expired";
                        expiredSessions.push(sessionId);
                    }
                }
            }

            // End expired sessions
            for (const sessionId of expiredSessions) {
                this.endVRSession(sessionId);
                console.log(`⏰ Ended expired VR session: ${sessionId}`);
            }

        } catch (error) {
            console.error('⚠️ Session cleanup error:', error.message);
        }
    }

    getVRCoreStatus() {
        return {
            totalDevices: this.devices.size,
            activeDevices: Array.from(this.devices.values()).filter(d => d.status === "connected").length,
            totalSessions: this.sessions.size,
            activeSessions: Array.from(this.sessions.values()).filter(s => s.status === "active").length,
            totalProjects: this.projects.size,
            config: this.config,
            quantumIntegration: this.config.enableQuantumIntegration,
            aiAssistance: this.config.enableAiAssistance
        };
    }

    generateId() {
        return Math.random().toString(36).substring(2, 15) +
               Math.random().toString(36).substring(2, 15);
    }
}

const app = express();
app.use(express.json());
app.use(morgan('dev'));
app.use(cors({ origin: true, credentials: true }));

// Initialize VR Core
let vrCore = null;
try {
    // Initialize VR core (JavaScript version)
    vrCore = new OmniVRCoreJS();
    console.log('🎮 VR Core initialized successfully');
} catch (error) {
    console.error('❌ Failed to initialize VR Core:', error.message);
}

// Health
app.get('/oauth2/health', (req, res) => {
  res.json({ ok: true, service: 'oauth2', timestamp: new Date().toISOString() });
});

// OAuth callbacks (stubs – implement token exchange when client secrets are provided)
app.get('/oauth2/callback/google', async (req, res) => {
  const { code, state } = req.query;
  console.log('[OAuth] Google callback code:', code, 'state:', state);
  const axios = require('axios');
  const fs = require('fs');
  const path = require('path');
  const OAUTH_REDIRECT_BASE = process.env.OAUTH_REDIRECT_BASE || 'https://localhost:3443';
  const TOKENS_FILE = path.join(__dirname, 'data', 'oauth_tokens.json');
  function saveToken(name, obj) {
    try {
      const dir = path.dirname(TOKENS_FILE);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      let existing = {};
      if (fs.existsSync(TOKENS_FILE)) {
        existing = JSON.parse(fs.readFileSync(TOKENS_FILE, 'utf8') || '{}');
      }
      existing[name] = obj;
      fs.writeFileSync(TOKENS_FILE, JSON.stringify(existing, null, 2));
    } catch (e) {
      console.error('Failed to save token', e);
    }
  }
  const clientId = process.env.GOOGLE_CLIENT_ID || process.env.YOUTUBE_CLIENT_ID || process.env.GOOGLEDRIVE_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET || process.env.YOUTUBE_CLIENT_SECRET || process.env.GOOGLEDRIVE_CLIENT_SECRET;
  const redirectUri = `${OAUTH_REDIRECT_BASE}/oauth2/callback/google`;
  if (!clientId || !clientSecret) {
    return res.status(400).json({ ok: false, reason: 'missing_client_config', message: 'Set GOOGLE_* or YOUTUBE_* or GOOGLEDRIVE_* client ID/secret in .env' });
  }
  if (!code) return res.status(400).json({ ok: false, reason: 'missing_code' });
  try {
    const params = new URLSearchParams({
      code,
      client_id: clientId,
      client_secret: clientSecret,
      redirect_uri: redirectUri,
      grant_type: 'authorization_code'
    });
    const r = await axios.post('https://oauth2.googleapis.com/token', params.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    saveToken('google', r.data);
    return res.json({ ok: true, token: { access_token: r.data.access_token, expires_in: r.data.expires_in } });
  } catch (e) {
    console.error('Google token exchange failed:', e.response?.data || e.message);
    return res.status(e.response?.status || 500).json({ ok: false, error: e.response?.data || e.message });
  }
});

// YouTube uses Google OAuth
app.get('/oauth2/callback/youtube', async (req, res) => {
  const { code, state } = req.query;
  console.log('[OAuth] YouTube callback code:', code, 'state:', state);
  const axios = require('axios');
  const fs = require('fs');
  const path = require('path');
  const OAUTH_REDIRECT_BASE = process.env.OAUTH_REDIRECT_BASE || 'https://localhost:3443';
  const TOKENS_FILE = path.join(__dirname, 'data', 'oauth_tokens.json');
  function saveToken(name, obj) {
    try {
      const dir = path.dirname(TOKENS_FILE);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      let existing = {};
      if (fs.existsSync(TOKENS_FILE)) {
        existing = JSON.parse(fs.readFileSync(TOKENS_FILE, 'utf8') || '{}');
      }
      existing[name] = obj;
      fs.writeFileSync(TOKENS_FILE, JSON.stringify(existing, null, 2));
    } catch (e) {
      console.error('Failed to save token', e);
    }
  }
  const clientId = process.env.YOUTUBE_CLIENT_ID || process.env.GOOGLE_CLIENT_ID;
  const clientSecret = process.env.YOUTUBE_CLIENT_SECRET || process.env.GOOGLE_CLIENT_SECRET;
  const redirectUri = `${OAUTH_REDIRECT_BASE}/oauth2/callback/youtube`;
  if (!clientId || !clientSecret) {
    return res.status(400).json({ ok: false, reason: 'missing_client_config', message: 'Set YOUTUBE_* client ID/secret in .env' });
  }
  if (!code) return res.status(400).json({ ok: false, reason: 'missing_code' });
  try {
    const params = new URLSearchParams({
      code,
      client_id: clientId,
      client_secret: clientSecret,
      redirect_uri: redirectUri,
      grant_type: 'authorization_code'
    });
    const r = await axios.post('https://oauth2.googleapis.com/token', params.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    saveToken('youtube', r.data);
    return res.json({ ok: true, token: { access_token: r.data.access_token, expires_in: r.data.expires_in } });
  } catch (e) {
    console.error('YouTube token exchange failed:', e.response?.data || e.message);
    return res.status(e.response?.status || 500).json({ ok: false, error: e.response?.data || e.message });
  }
});

app.get('/oauth2/callback/tiktok', async (req, res) => {
  const { code, state } = req.query;
  console.log('[OAuth] TikTok callback code:', code, 'state:', state);
  const axios = require('axios');
  const fs = require('fs');
  const path = require('path');
  const OAUTH_REDIRECT_BASE = process.env.OAUTH_REDIRECT_BASE || 'https://localhost:3443';
  const TOKENS_FILE = path.join(__dirname, 'data', 'oauth_tokens.json');
  function saveToken(name, obj) {
    try {
      const dir = path.dirname(TOKENS_FILE);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      let existing = {};
      if (fs.existsSync(TOKENS_FILE)) {
        existing = JSON.parse(fs.readFileSync(TOKENS_FILE, 'utf8') || '{}');
      }
      existing[name] = obj;
      fs.writeFileSync(TOKENS_FILE, JSON.stringify(existing, null, 2));
    } catch (e) {
      console.error('Failed to save token', e);
    }
  }
  const clientKey = process.env.TIKTOK_CLIENT_KEY || process.env.TIKTOK_CLIENT_ID || process.env.TIKTOK_CLIENTID;
  const clientSecret = process.env.TIKTOK_CLIENT_SECRET;
  const redirectUri = `${OAUTH_REDIRECT_BASE}/oauth2/callback/tiktok`;
  if (!clientKey || !clientSecret) {
    return res.status(400).json({ ok: false, reason: 'missing_client_config', message: 'Set TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET in .env' });
  }
  if (!code) return res.status(400).json({ ok: false, reason: 'missing_code' });
  try {
    const params = new URLSearchParams({
      client_key: clientKey,
      client_secret: clientSecret,
      code,
      grant_type: 'authorization_code',
      redirect_uri: redirectUri
    });
    const r = await axios.post('https://open-api.tiktok.com/oauth/token', params.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    saveToken('tiktok', r.data);
    return res.json({ ok: true, token: { access_token: r.data.access_token, expires_in: r.data.expires_in } });
  } catch (e) {
    console.error('TikTok token exchange failed:', e.response?.data || e.message);
    return res.status(e.response?.status || 500).json({ ok: false, error: e.response?.data || e.message });
  }
});

// HAL endpoints (mock)
app.get('/hw/health', (req, res) => {
  res.json({ ok: true, service: 'hw-hal', timestamp: new Date().toISOString() });
});

app.get('/hw/scan', async (req, res) => {
  const devices = await HAL.scan();
  res.json({ ok: true, devices });
});

app.post('/hw/mock/connect', async (req, res) => {
  const { id } = req.body;
  const ok = await HAL.connect(id || 'mock-1');
  res.json({ ok });
});

app.post('/hw/mock/write', async (req, res) => {
  const { data } = req.body;
  const ok = await HAL.write(data || 'hello');
  res.json({ ok });
});

app.get('/hw/mock/read', async (req, res) => {
  const out = await HAL.read();
  res.json({ ok: true, data: out });
});

// Google Drive callback
app.get('/oauth2/callback/googledrive', async (req, res) => {
  const { code, state } = req.query;
  console.log('[OAuth] Google Drive callback code:', code, 'state:', state);
  const axios = require('axios');
  const fs = require('fs');
  const path = require('path');
  const OAUTH_REDIRECT_BASE = process.env.OAUTH_REDIRECT_BASE || 'https://localhost:3443';
  const TOKENS_FILE = path.join(__dirname, 'data', 'oauth_tokens.json');
  function saveToken(name, obj) {
    try {
      const dir = path.dirname(TOKENS_FILE);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      let existing = {};
      if (fs.existsSync(TOKENS_FILE)) {
        existing = JSON.parse(fs.readFileSync(TOKENS_FILE, 'utf8') || '{}');
      }
      existing[name] = obj;
      fs.writeFileSync(TOKENS_FILE, JSON.stringify(existing, null, 2));
    } catch (e) {
      console.error('Failed to save token', e);
    }
  }
  const clientId = process.env.GOOGLEDRIVE_CLIENT_ID || process.env.GOOGLE_CLIENT_ID;
  const clientSecret = process.env.GOOGLEDRIVE_CLIENT_SECRET || process.env.GOOGLE_CLIENT_SECRET;
  const redirectUri = `${OAUTH_REDIRECT_BASE}/oauth2/callback/googledrive`;
  if (!clientId || !clientSecret) {
    return res.status(400).json({ ok: false, reason: 'missing_client_config', message: 'Set GOOGLEDRIVE_* client ID/secret in .env' });
  }
  if (!code) return res.status(400).json({ ok: false, reason: 'missing_code' });
  try {
    const params = new URLSearchParams({
      code,
      client_id: clientId,
      client_secret: clientSecret,
      redirect_uri: redirectUri,
      grant_type: 'authorization_code'
    });
    const r = await axios.post('https://oauth2.googleapis.com/token', params.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    saveToken('googledrive', r.data);
    return res.json({ ok: true, token: { access_token: r.data.access_token, expires_in: r.data.expires_in } });
  } catch (e) {
    console.error('Google Drive token exchange failed:', e.response?.data || e.message);
    return res.status(e.response?.status || 500).json({ ok: false, error: e.response?.data || e.message });
  }
});

// ==================== VR API ROUTES ====================

// VR Core Status
app.get('/vr/status', (req, res) => {
  try {
    if (!vrCore) {
      return res.status(503).json({ error: 'VR Core not initialized' });
    }
    const status = vrCore.getVRCoreStatus();
    res.json({ ok: true, vr_status: status });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// List VR Projects
app.get('/vr/projects', (req, res) => {
  try {
    if (!vrCore) {
      return res.status(503).json({ error: 'VR Core not initialized' });
    }
    const projects = vrCore.getVRProjectsList();
    res.json({ ok: true, projects });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Register VR Device
app.post('/vr/devices/register', (req, res) => {
  try {
    if (!vrCore) {
      return res.status(503).json({ error: 'VR Core not initialized' });
    }

    const { deviceInfo, userId } = req.body;
    if (!deviceInfo || !userId) {
      return res.status(400).json({ error: 'deviceInfo and userId are required' });
    }

    const deviceId = vrCore.registerVRDevice(deviceInfo, userId);
    if (!deviceId) {
      return res.status(500).json({ error: 'Failed to register VR device' });
    }

    res.json({ ok: true, deviceId });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get VR Device Status
app.get('/vr/devices/:deviceId/status', (req, res) => {
  try {
    if (!vrCore) {
      return res.status(503).json({ error: 'VR Core not initialized' });
    }

    const { deviceId } = req.params;
    const status = vrCore.getVRDeviceStatus(deviceId);

    if (status.error) {
      return res.status(404).json(status);
    }

    res.json({ ok: true, device_status: status });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create VR Session
app.post('/vr/sessions/create', (req, res) => {
  try {
    if (!vrCore) {
      return res.status(503).json({ error: 'VR Core not initialized' });
    }

    const { deviceId, projectId, userId } = req.body;
    if (!deviceId || !projectId || !userId) {
      return res.status(400).json({ error: 'deviceId, projectId, and userId are required' });
    }

    const sessionId = vrCore.createVRSession(deviceId, projectId, userId);
    if (!sessionId) {
      return res.status(500).json({ error: 'Failed to create VR session' });
    }

    res.json({ ok: true, sessionId });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get VR Session Info
app.get('/vr/sessions/:sessionId', (req, res) => {
  try {
    if (!vrCore) {
      return res.status(503).json({ error: 'VR Core not initialized' });
    }

    const { sessionId } = req.params;
    const sessionInfo = vrCore.getVRSessionInfo(sessionId);

    if (sessionInfo.error) {
      return res.status(404).json(sessionInfo);
    }

    res.json({ ok: true, session_info: sessionInfo });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// End VR Session
app.post('/vr/sessions/:sessionId/end', (req, res) => {
  try {
    if (!vrCore) {
      return res.status(503).json({ error: 'VR Core not initialized' });
    }

    const { sessionId } = req.params;
    const success = vrCore.endVRSession(sessionId);

    if (!success) {
      return res.status(404).json({ error: 'Session not found or already ended' });
    }

    res.json({ ok: true, message: 'VR session ended successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// VR Project Access (serve VR files)
app.get('/vr/projects/:projectId', (req, res) => {
  try {
    const { projectId } = req.params;

    // Map project IDs to actual files
    let filePath = '';
    if (projectId === 'example_trampoline_game') {
      filePath = 'vr_projects/templates/threejs_basic.html';
    } else if (projectId === 'example_art_gallery') {
      filePath = 'vr_projects/templates/aframe_basic.html';
    } else if (projectId === 'example_meditation_space') {
      filePath = 'vr_projects/templates/threejs_basic.html';
    } else {
      return res.status(404).json({ error: 'VR project not found' });
    }

    const fs = require('fs');
    const path = require('path');

    const fullPath = path.join(__dirname, filePath);
    if (fs.existsSync(fullPath)) {
      res.sendFile(fullPath);
    } else {
      res.status(404).json({ error: 'VR project file not found' });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// VR WebSocket for real-time communication
const WebSocket = require('ws');
const vrWSS = new WebSocket.Server({ noServer: true });

vrWSS.on('connection', (ws, request) => {
  console.log('🎮 VR WebSocket client connected');

  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message.toString());

      switch (data.type) {
        case 'register_device':
          if (vrCore && data.deviceInfo && data.userId) {
            const deviceId = vrCore.registerVRDevice(data.deviceInfo, data.userId);
            ws.send(JSON.stringify({
              type: 'device_registered',
              deviceId,
              success: true
            }));
          }
          break;

        case 'heartbeat':
          if (vrCore && data.deviceId) {
            const device = vrCore.devices.get(data.deviceId);
            if (device) {
              device.lastSeen = new Date();
            }
          }
          break;

        case 'session_update':
          if (vrCore && data.sessionId) {
            const session = vrCore.sessions.get(data.sessionId);
            if (session) {
              session.metrics = { ...session.metrics, ...data.metrics };
            }
          }
          break;

        default:
          console.log('🎮 Unknown VR WebSocket message type:', data.type);
      }
    } catch (error) {
      console.error('🎮 VR WebSocket error:', error.message);
    }
  });

  ws.on('close', () => {
    console.log('🎮 VR WebSocket client disconnected');
  });
});

// Handle WebSocket upgrade for VR
app.on('upgrade', (request, socket, head) => {
  if (request.url === '/vr/websocket') {
    vrWSS.handleUpgrade(request, socket, head, (ws) => {
      vrWSS.emit('connection', ws, request);
    });
  } else {
    socket.destroy();
  }
});

const port = process.env.OAUTH_PORT || 3090;
app.listen(port, () => {
  console.log(`OAuth/HAL/VR microservice listening on http://localhost:${port}`);
  console.log(`🎮 VR API endpoints available at:`);
  console.log(`   - VR Status: http://localhost:${port}/vr/status`);
  console.log(`   - VR Projects: http://localhost:${port}/vr/projects`);
  console.log(`   - VR WebSocket: ws://localhost:${port}/vr/websocket`);
});