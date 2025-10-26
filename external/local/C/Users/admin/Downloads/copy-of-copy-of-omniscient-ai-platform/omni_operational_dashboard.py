#!/usr/bin/env python3
"""
OMNI PLATFORM - PROFESSIONAL OPERATIONAL DASHBOARD
Complete monitoring, analytics, and management system for the entire Omni AI platform
"""

import asyncio
import json
import time
import psutil
import socket
import platform
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
import queue
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

# Web framework
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Monitoring and visualization
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

# Import quantum singularity components
try:
    from omni_singularity_core import (
        initialize_omni_singularity_core,
        process_omni_command,
        get_omni_core_status,
        omni_singularity_core
    )
    QUANTUM_SINGULARITY_AVAILABLE = True
except ImportError:
    QUANTUM_SINGULARITY_AVAILABLE = False
    logger.warning("Quantum Singularity components not available")

# Import OMNI platform client and authentication
try:
    from omni_platform_api_client import get_omni_client, OmniPlatformError
    from omni_auth import get_omni_authenticator, AuthConfig, AuthMethod
    OMNI_PLATFORM_AVAILABLE = True
except ImportError:
    OMNI_PLATFORM_AVAILABLE = False
    logger.warning("OMNI Platform client not available")

# Configure logging
import os
log_dir = '/opt/omni/logs' if os.path.exists('/opt/omni') else './logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'omni_dashboard.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"
    UNKNOWN = "unknown"

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    load_average: List[float]
    process_count: int

@dataclass
class ServiceInfo:
    """Information about a specific service"""
    name: str
    status: ServiceStatus
    uptime: Optional[timedelta]
    last_check: datetime
    response_time: Optional[float]
    error_rate: float
    version: str

@dataclass
class CloudResource:
    """Google Cloud resource information"""
    instance_name: str
    instance_type: str
    status: str
    external_ip: str
    zone: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    cost_per_hour: float

@dataclass
class OmniPlatformData:
    """OMNI platform specific data"""
    platform_status: Optional[str]
    gemini_model: str
    total_requests: int
    success_rate: float
    avg_response_time: float
    last_activity: Optional[datetime]
    error_count: int
    features: List[str]

class OmniOperationalDashboard:
    """
    Professional operational dashboard for the complete Omni AI platform
    """

    def __init__(self):
        self.app = FastAPI(
            title="OMNI Platform Dashboard",
            description="Professional operational dashboard for the complete Omni AI platform",
            version="2.0.0"
        )

        # Data storage
        self.metrics_history: List[SystemMetrics] = []
        self.services: Dict[str, ServiceInfo] = {}
        self.cloud_resources: List[CloudResource] = []
        self.alerts: List[Dict[str, Any]] = []
        self.omni_platform_data: Optional[OmniPlatformData] = None

        # WebSocket connections for real-time updates
        self.websocket_connections: List[WebSocket] = []
        self.websocket_update_interval = 5  # seconds

        # OMNI platform client and authentication
        self.omni_client = None
        self.omni_auth = None

        if OMNI_PLATFORM_AVAILABLE:
            try:
                # Initialize authenticator
                self.omni_auth = get_omni_authenticator()
                logger.info("OMNI Platform authenticator initialized successfully")

                # Initialize client with authentication
                self.omni_client = get_omni_client()
                logger.info("OMNI Platform client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OMNI Platform components: {e}")

        # Configuration
        self.max_metrics_history = 1000
        self.check_interval = 30  # seconds
        self.cost_per_hour = {
            'n1-standard-8': 0.38,
            'n1-standard-2': 0.095,
            'e2-medium': 0.033
        }

        # Setup routes
        self._setup_routes()

        # Start background monitoring
        self.monitoring_active = False

    def _setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Main dashboard interface"""
            return self._generate_dashboard_html()

        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get current system metrics"""
            return JSONResponse(content={
                "metrics": [asdict(m) for m in self.metrics_history[-100:]],  # Last 100 readings
                "summary": self._get_metrics_summary()
            })

        @self.app.get("/api/services")
        async def get_services():
            """Get services status"""
            return JSONResponse(content={
                "services": {name: asdict(service) for name, service in self.services.items()},
                "overall_health": self._calculate_overall_health()
            })

        @self.app.get("/api/cloud")
        async def get_cloud_resources():
            """Get Google Cloud resources information"""
            return JSONResponse(content={
                "resources": [asdict(r) for r in self.cloud_resources],
                "total_cost_per_hour": sum(r.cost_per_hour for r in self.cloud_resources),
                "total_cost_per_day": sum(r.cost_per_hour * 24 for r in self.cloud_resources)
            })

        @self.app.get("/api/alerts")
        async def get_alerts():
            """Get active alerts"""
            return JSONResponse(content={
                "alerts": self.alerts[-50:],  # Last 50 alerts
                "critical_count": len([a for a in self.alerts if a["severity"] == "critical"]),
                "warning_count": len([a for a in self.alerts if a["severity"] == "warning"])
            })

        @self.app.get("/api/analytics")
        async def get_analytics():
            """Get platform analytics"""
            return JSONResponse(content=self._generate_analytics())

        @self.app.get("/api/omni")
        async def get_omni_platform_data():
            """Get OMNI platform specific data"""
            return JSONResponse(content=self._get_omni_platform_data())

        @self.app.get("/api/omni/status")
        async def get_omni_status():
            """Get OMNI platform status"""
            return JSONResponse(content=self._get_omni_status())

        @self.app.post("/api/omni/chat")
        async def send_omni_chat(request: dict):
            """Send chat message to OMNI platform"""
            if not self.omni_client:
                raise HTTPException(status_code=503, detail="OMNI Platform not available")

            message = request.get('message', '')
            if not message:
                raise HTTPException(status_code=400, detail="Message is required")

            try:
                result = self.omni_client.send_chat_message(message)
                return JSONResponse(content=result)
            except OmniPlatformError as e:
                raise HTTPException(status_code=502, detail=str(e))

        @self.app.post("/api/services/{service_name}/restart")
        async def restart_service(service_name: str):
            """Restart a specific service"""
            if service_name in self.services:
                success = await self._restart_service(service_name)
                if success:
                    return {"message": f"Service {service_name} restarted successfully"}
                else:
                    raise HTTPException(status_code=500, detail=f"Failed to restart {service_name}")
            else:
                raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time dashboard updates"""
            await websocket.accept()
            self.websocket_connections.append(websocket)

            try:
                while True:
                    # Send real-time data to connected clients
                    await self._broadcast_realtime_data(websocket)
                    await asyncio.sleep(self.websocket_update_interval)
            except WebSocketDisconnect:
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)

    def _generate_dashboard_html(self) -> str:
        """Generate the main dashboard HTML interface"""
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>OMNI Platform - Operational Dashboard</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                }
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }
                .metrics-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .metric-card {
                    background: rgba(255,255,255,0.1);
                    padding: 20px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255,255,255,0.2);
                }
                .metric-title {
                    font-size: 14px;
                    opacity: 0.8;
                    margin-bottom: 10px;
                }
                .metric-value {
                    font-size: 28px;
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                .metric-change {
                    font-size: 12px;
                    opacity: 0.7;
                }
                .status-indicator {
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    margin-right: 8px;
                }
                .status-healthy { background-color: #4CAF50; }
                .status-warning { background-color: #FF9800; }
                .status-critical { background-color: #F44336; }
                .status-offline { background-color: #9E9E9E; }
                .charts-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .chart-container {
                    background: rgba(255,255,255,0.1);
                    padding: 20px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }
                .services-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 15px;
                }
                .service-card {
                    background: rgba(255,255,255,0.1);
                    padding: 15px;
                    border-radius: 10px;
                    border: 1px solid rgba(255,255,255,0.2);
                }
                .service-name {
                    font-weight: bold;
                    margin-bottom: 8px;
                }
                .service-status {
                    display: flex;
                    align-items: center;
                    margin-bottom: 5px;
                }
                .service-uptime {
                    font-size: 12px;
                    opacity: 0.7;
                }
                .refresh-btn {
                    background: rgba(255,255,255,0.2);
                    border: none;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 8px;
                    cursor: pointer;
                    margin: 10px;
                }
                .refresh-btn:hover {
                    background: rgba(255,255,255,0.3);
                }
                .alerts-section {
                    background: rgba(255,255,255,0.1);
                    padding: 20px;
                    border-radius: 15px;
                    margin-top: 20px;
                }
                .section-title {
                    font-size: 20px;
                    font-weight: bold;
                    margin: 30px 0 20px 0;
                    color: #4ECDC4;
                    text-align: center;
                }
                .omni-platform-section {
                    background: rgba(255,255,255,0.1);
                    padding: 20px;
                    border-radius: 15px;
                    margin: 20px 0;
                }
                .omni-feature-list {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 10px;
                    margin-top: 15px;
                }
                .omni-feature-item {
                    background: rgba(255,255,255,0.1);
                    padding: 10px;
                    border-radius: 8px;
                    text-align: center;
                    font-size: 12px;
                }
                .alert-item {
                    background: rgba(255,255,255,0.1);
                    padding: 10px;
                    margin: 5px 0;
                    border-radius: 5px;
                    border-left: 4px solid #FF9800;
                }
                .alert-critical { border-left-color: #F44336; }
                .alert-warning { border-left-color: #FF9800; }
                .alert-info { border-left-color: #2196F3; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>OMNI Platform - Operational Dashboard</h1>
                    <p>Professional monitoring and management interface</p>
                    <button class="refresh-btn" onclick="refreshAll()">Refresh All</button>
                </div>

                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-title">System Health</div>
                        <div class="metric-value" id="overallHealth">Loading...</div>
                        <div class="metric-change" id="healthChange">Calculating...</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Monthly Cost Estimate</div>
                        <div class="metric-value" id="monthlyCost">$0.00</div>
                        <div class="metric-change" id="costChange">Free tier active</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Active Services</div>
                        <div class="metric-value" id="activeServices">0/0</div>
                        <div class="metric-change" id="servicesChange">Initializing...</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Avg Response Time</div>
                        <div class="metric-value" id="avgResponse">0ms</div>
                        <div class="metric-change" id="responseChange">Monitoring...</div>
                    </div>
                </div>

                <!-- OMNI Platform Metrics Section -->
                <div class="section-title">OMNI Platform Status</div>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-title">OMNI Platform Status</div>
                        <div class="metric-value" id="omniStatus">Loading...</div>
                        <div class="metric-change" id="omniStatusChange">Checking...</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">AI Model</div>
                        <div class="metric-value" id="omniModel">Unknown</div>
                        <div class="metric-change" id="omniModelChange">Loading...</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Success Rate</div>
                        <div class="metric-value" id="omniSuccessRate">0%</div>
                        <div class="metric-change" id="omniSuccessChange">Calculating...</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Avg Response Time</div>
                        <div class="metric-value" id="omniResponseTime">0ms</div>
                        <div class="metric-change" id="omniResponseChange">Monitoring...</div>
                    </div>
                </div>

                <div class="charts-grid">
                    <div class="chart-container">
                        <h3>CPU & Memory Usage</h3>
                        <div id="systemChart"></div>
                    </div>
                    <div class="chart-container">
                        <h3>Disk Usage</h3>
                        <div id="diskChart"></div>
                    </div>
                </div>

                <div class="charts-grid">
                    <div class="chart-container">
                        <h3>Service Status</h3>
                        <div class="services-grid" id="servicesContainer">
                            <p>Loading services...</p>
                        </div>
                    </div>
                    <div class="chart-container">
                        <h3>Recent Alerts</h3>
                        <div id="alertsContainer">
                            <p>Loading alerts...</p>
                        </div>
                    </div>
                </div>

                <div class="omni-platform-section">
                    <h3>OMNI Platform Details</h3>
                    <div class="omni-feature-list" id="omniFeatures">
                        <p>Loading OMNI platform features...</p>
                    </div>
                    <div style="margin-top: 20px;">
                        <h4>Platform Services</h4>
                        <div id="omniServices">
                            <p>Loading OMNI platform services...</p>
                        </div>
                    </div>
                </div>

                <div class="alerts-section">
                    <h3>System Information</h3>
                    <div id="systemInfo">
                        <p>Loading system information...</p>
                    </div>
                </div>
            </div>

            <script>
                // Dashboard update functions
                async function refreshAll() {
                    await Promise.all([
                        updateMetrics(),
                        updateServices(),
                        updateAlerts(),
                        updateSystemInfo(),
                        updateOmniPlatform()
                    ]);
                }

                async function updateMetrics() {
                    try {
                        const response = await fetch('/api/metrics');
                        const data = await response.json();

                        // Update overall health
                        const health = data.summary.overall_health;
                        document.getElementById('overallHealth').textContent = health.charAt(0).toUpperCase() + health.slice(1);

                        // Update cost information
                        const cost = data.summary.estimated_cost_per_day;
                        document.getElementById('monthlyCost').textContent = '$' + (cost * 30).toFixed(2);

                        // Update system charts
                        updateSystemChart(data.metrics);
                        updateDiskChart(data.summary.disk_usage);

                    } catch (error) {
                        console.error('Error updating metrics:', error);
                    }
                }

                async function updateServices() {
                    try {
                        const response = await fetch('/api/services');
                        const data = await response.json();

                        const servicesContainer = document.getElementById('servicesContainer');
                        const services = data.services;

                        let html = '';
                        for (const [name, service] of Object.entries(services)) {
                            const statusClass = 'status-' + service.status;
                            html += `
                                <div class="service-card">
                                    <div class="service-name">${name}</div>
                                    <div class="service-status">
                                        <span class="status-indicator ${statusClass}"></span>
                                        ${service.status.charAt(0).toUpperCase() + service.status.slice(1)}
                                    </div>
                                    <div class="service-uptime">Uptime: ${service.uptime || 'Unknown'}</div>
                                </div>
                            `;
                        }

                        servicesContainer.innerHTML = html;

                        // Update active services count
                        const activeCount = Object.values(services).filter(s => s.status === 'healthy').length;
                        const totalCount = Object.keys(services).length;
                        document.getElementById('activeServices').textContent = `${activeCount}/${totalCount}`;

                    } catch (error) {
                        console.error('Error updating services:', error);
                    }
                }

                async function updateAlerts() {
                    try {
                        const response = await fetch('/api/alerts');
                        const data = await response.json();

                        const alertsContainer = document.getElementById('alertsContainer');
                        const alerts = data.alerts;

                        let html = '';
                        alerts.slice(-10).forEach(alert => {
                            const alertClass = 'alert-' + alert.severity;
                            html += `
                                <div class="alert-item ${alertClass}">
                                    <strong>${alert.severity.toUpperCase()}</strong>: ${alert.message}
                                    <br><small>${new Date(alert.timestamp).toLocaleString()}</small>
                                </div>
                            `;
                        });

                        alertsContainer.innerHTML = html;

                    } catch (error) {
                        console.error('Error updating alerts:', error);
                    }
                }

                async function updateSystemInfo() {
                    try {
                        const response = await fetch('/api/cloud');
                        const data = await response.json();

                        let html = '<div class="cloud-resources">';
                        data.resources.forEach(resource => {
                            html += `
                                <div class="resource-item">
                                    <strong>${resource.instance_name}</strong><br>
                                    Type: ${resource.instance_type}<br>
                                    Status: ${resource.status}<br>
                                    IP: ${resource.external_ip}<br>
                                    CPU: ${resource.cpu_usage.toFixed(1)}%<br>
                                    Memory: ${resource.memory_usage.toFixed(1)}%<br>
                                    Cost/Hour: $${resource.cost_per_hour}
                                </div>
                            `;
                        });
                        html += '</div>';

                        document.getElementById('systemInfo').innerHTML = html;

                    } catch (error) {
                        console.error('Error updating system info:', error);
                    }
                }

                async function updateOmniPlatform() {
                    try {
                        const response = await fetch('/api/omni');
                        const data = await response.json();

                        if (data.error) {
                            document.getElementById('omniStatus').textContent = 'Error';
                            document.getElementById('omniStatusChange').textContent = data.error;
                            return;
                        }

                        // Update OMNI platform metrics
                        document.getElementById('omniStatus').textContent = data.platform_status || 'Unknown';
                        document.getElementById('omniModel').textContent = data.gemini_model || 'Unknown';
                        document.getElementById('omniSuccessRate').textContent = data.success_rate ? data.success_rate.toFixed(1) + '%' : '0%';
                        document.getElementById('omniResponseTime').textContent = data.avg_response_time ? Math.round(data.avg_response_time) + 'ms' : '0ms';

                        // Update features list
                        const featuresContainer = document.getElementById('omniFeatures');
                        let featuresHtml = '';
                        if (data.features && data.features.length > 0) {
                            data.features.forEach(feature => {
                                featuresHtml += `<div class="omni-feature-item">${feature}</div>`;
                            });
                        } else {
                            featuresHtml = '<p>No features available</p>';
                        }
                        featuresContainer.innerHTML = featuresHtml;

                        // Update services
                        const servicesContainer = document.getElementById('omniServices');
                        let servicesHtml = '';
                        if (data.services) {
                            for (const [service, status] of Object.entries(data.services)) {
                                servicesHtml += `
                                    <div class="service-card">
                                        <div class="service-name">${service}</div>
                                        <div class="service-status">
                                            <span class="status-indicator status-${status === 'active' ? 'healthy' : 'offline'}"></span>
                                            ${status}
                                        </div>
                                    </div>
                                `;
                            }
                        } else {
                            servicesHtml = '<p>No service information available</p>';
                        }
                        servicesContainer.innerHTML = servicesHtml;

                    } catch (error) {
                        console.error('Error updating OMNI platform data:', error);
                        document.getElementById('omniStatus').textContent = 'Error';
                        document.getElementById('omniStatusChange').textContent = 'Failed to fetch data';
                    }
                }

                function updateSystemChart(metrics) {
                    const timestamps = metrics.map(m => new Date(m.timestamp));
                    const cpuData = metrics.map(m => m.cpu_percent);
                    const memoryData = metrics.map(m => m.memory_percent);

                    const trace1 = {
                        x: timestamps,
                        y: cpuData,
                        name: 'CPU Usage',
                        type: 'scatter',
                        line: { color: '#FF6B6B' }
                    };

                    const trace2 = {
                        x: timestamps,
                        y: memoryData,
                        name: 'Memory Usage',
                        type: 'scatter',
                        line: { color: '#4ECDC4' }
                    };

                    const layout = {
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { color: 'white' },
                        margin: { t: 20, r: 20, b: 40, l: 40 },
                        xaxis: { title: 'Time' },
                        yaxis: { title: 'Usage %' }
                    };

                    Plotly.newPlot('systemChart', [trace1, trace2], layout);
                }

                function updateDiskChart(diskUsage) {
                    const data = [{
                        values: [diskUsage.used_percent, 100 - diskUsage.used_percent],
                        labels: ['Used', 'Available'],
                        type: 'pie',
                        marker: {
                            colors: ['#FF6B6B', '#4ECDC4']
                        }
                    }];

                    const layout = {
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { color: 'white' },
                        margin: { t: 20, r: 20, b: 20, l: 20 }
                    };

                    Plotly.newPlot('diskChart', data, layout);
                }

                // WebSocket connection for real-time updates
                let websocket = null;

                function connectWebSocket() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//${window.location.host}/ws`;

                    websocket = new WebSocket(wsUrl);

                    websocket.onopen = function(event) {
                        console.log('WebSocket connected');
                    };

                    websocket.onmessage = function(event) {
                        try {
                            const data = JSON.parse(event.data);
                            handleRealtimeUpdate(data);
                        } catch (error) {
                            console.error('Error parsing WebSocket data:', error);
                        }
                    };

                    websocket.onclose = function(event) {
                        console.log('WebSocket disconnected, reconnecting...');
                        // Reconnect after 5 seconds
                        setTimeout(connectWebSocket, 5000);
                    };

                    websocket.onerror = function(error) {
                        console.error('WebSocket error:', error);
                    };
                }

                function handleRealtimeUpdate(data) {
                    // Update metrics in real-time
                    if (data.metrics) {
                        const health = data.metrics.overall_health;
                        document.getElementById('overallHealth').textContent = health.charAt(0).toUpperCase() + health.slice(1);

                        const cost = data.metrics.estimated_cost_per_day;
                        document.getElementById('monthlyCost').textContent = '$' + (cost * 30).toFixed(2);
                    }

                    // Update OMNI platform data in real-time
                    if (data.omni_platform && !data.omni_platform.error) {
                        document.getElementById('omniStatus').textContent = data.omni_platform.platform_status || 'Unknown';
                        document.getElementById('omniModel').textContent = data.omni_platform.gemini_model || 'Unknown';
                        document.getElementById('omniSuccessRate').textContent = data.omni_platform.success_rate ? data.omni_platform.success_rate.toFixed(1) + '%' : '0%';
                        document.getElementById('omniResponseTime').textContent = data.omni_platform.avg_response_time ? Math.round(data.omni_platform.avg_response_time) + 'ms' : '0ms';
                    }

                    // Update alerts in real-time
                    if (data.alerts) {
                        const alertsContainer = document.getElementById('alertsContainer');
                        let html = '';
                        data.alerts.slice(-5).forEach(alert => {
                            const alertClass = 'alert-' + alert.severity;
                            html += `
                                <div class="alert-item ${alertClass}">
                                    <strong>${alert.severity.toUpperCase()}</strong>: ${alert.message}
                                    <br><small>${new Date(alert.timestamp).toLocaleString()}</small>
                                </div>
                            `;
                        });
                        alertsContainer.innerHTML = html;
                    }
                }

                // Connect to WebSocket for real-time updates
                connectWebSocket();

                // Fallback to polling if WebSocket fails
                setInterval(refreshAll, 30000);

                // Initial load
                refreshAll();
            </script>
        </body>
        </html>
        """
        return html

    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics"""
        if not self.metrics_history:
            return {
                "overall_health": "unknown",
                "estimated_cost_per_day": 0,
                "disk_usage": {"used_percent": 0}
            }

        latest = self.metrics_history[-1]

        # Calculate overall health
        health_score = 100
        if latest.cpu_percent > 80: health_score -= 30
        if latest.memory_percent > 80: health_score -= 30
        if latest.disk_usage_percent > 80: health_score -= 20

        if health_score >= 80:
            overall_health = "healthy"
        elif health_score >= 60:
            overall_health = "warning"
        else:
            overall_health = "critical"

        # Estimate daily cost
        estimated_cost_per_day = sum(r.cost_per_hour * 24 for r in self.cloud_resources)

        return {
            "overall_health": overall_health,
            "estimated_cost_per_day": estimated_cost_per_day,
            "disk_usage": {"used_percent": latest.disk_usage_percent}
        }

    def _calculate_overall_health(self) -> str:
        """Calculate overall platform health"""
        if not self.services:
            return "unknown"

        healthy_count = sum(1 for s in self.services.values() if s.status == ServiceStatus.HEALTHY)
        total_count = len(self.services)

        if healthy_count == total_count:
            return "healthy"
        elif healthy_count >= total_count * 0.7:
            return "warning"
        else:
            return "critical"

    def _generate_analytics(self) -> Dict[str, Any]:
        """Generate comprehensive analytics"""
        if not self.metrics_history:
            return {"error": "No metrics data available"}

        # Extract data for analysis
        cpu_data = [m.cpu_percent for m in self.metrics_history]
        memory_data = [m.memory_percent for m in self.metrics_history]

        return {
            "performance": {
                "avg_cpu": statistics.mean(cpu_data),
                "max_cpu": max(cpu_data),
                "avg_memory": statistics.mean(memory_data),
                "max_memory": max(memory_data),
                "uptime_days": self._get_uptime_days()
            },
            "predictions": {
                "estimated_monthly_cost": sum(r.cost_per_hour * 24 * 30 for r in self.cloud_resources),
                "resource_efficiency": self._calculate_efficiency()
            },
            "recommendations": self._generate_recommendations()
        }

    def _get_uptime_days(self) -> float:
        """Calculate system uptime in days"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                return uptime_seconds / (24 * 3600)
        except:
            return 0

    def _calculate_efficiency(self) -> float:
        """Calculate resource efficiency score"""
        if not self.metrics_history:
            return 0

        avg_cpu = statistics.mean(m.cpu_percent for m in self.metrics_history)
        avg_memory = statistics.mean(m.memory_percent for m in self.metrics_history)

        # Efficiency is higher when resources are well utilized but not overloaded
        efficiency = 100 - abs(avg_cpu - 70) - abs(avg_memory - 60)
        return max(0, min(100, efficiency))

    def _generate_recommendations(self) -> List[str]:
        """Generate operational recommendations"""
        recommendations = []

        if self.cloud_resources:
            total_cost = sum(r.cost_per_hour * 24 * 30 for r in self.cloud_resources)
            if total_cost > 200:
                recommendations.append("Consider optimizing instance sizes to reduce costs")
            if total_cost < 50:
                recommendations.append("Current setup is very cost-effective")

        if self.services:
            offline_services = [name for name, s in self.services.items() if s.status == ServiceStatus.OFFLINE]
            if offline_services:
                recommendations.append(f"Restart offline services: {', '.join(offline_services)}")

        # OMNI platform specific recommendations
        if self.omni_platform_data:
            if self.omni_platform_data.success_rate < 90:
                recommendations.append("OMNI Platform success rate is below 90% - investigate issues")
            if self.omni_platform_data.avg_response_time > 5000:  # 5 seconds
                recommendations.append("OMNI Platform response time is slow - consider optimization")

        return recommendations

    def _get_omni_platform_data(self) -> Dict[str, Any]:
        """Get OMNI platform data"""
        if not self.omni_client or not self.omni_auth:
            return {"error": "OMNI Platform components not available"}

        try:
            # Test authentication first
            if not self.omni_auth.test_connection():
                return {"error": "Authentication failed with OMNI platform"}

            # Get platform status
            status = self.omni_client.get_platform_status()

            # Get conversation metrics
            metrics = self.omni_client.get_conversation_metrics()

            return {
                "platform_status": status.status,
                "gemini_model": status.gemini_model,
                "total_requests": metrics.total_conversations,
                "success_rate": metrics.success_rate,
                "avg_response_time": metrics.avg_response_time,
                "last_activity": metrics.last_activity.isoformat() if metrics.last_activity else None,
                "error_count": metrics.error_count,
                "features": status.features,
                "services": status.services,
                "project_id": status.project_id,
                "deployment": status.deployment,
                "provider": status.provider,
                "authentication": "verified"
            }

        except Exception as e:
            logger.error(f"Error getting OMNI platform data: {e}")
            return {"error": f"Failed to get OMNI platform data: {str(e)}"}

    def _get_omni_status(self) -> Dict[str, Any]:
        """Get OMNI platform status"""
        if not self.omni_client:
            return {"error": "OMNI Platform client not available"}

        try:
            status = self.omni_client.get_platform_status()
            health = self.omni_client.get_health_status()

            return {
                "status": status.status,
                "platform": status.platform,
                "deployment": status.deployment,
                "provider": status.provider,
                "gemini_model": status.gemini_model,
                "services": status.services,
                "features": status.features,
                "health": health,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting OMNI status: {e}")
            return {"error": f"Failed to get OMNI status: {str(e)}"}

    def _update_omni_platform_data(self):
        """Update OMNI platform data in background"""
        if not self.omni_client:
            return

        try:
            # Get platform status
            status = self.omni_client.get_platform_status()

            # Get conversation metrics
            metrics = self.omni_client.get_conversation_metrics()

            # Update stored data
            self.omni_platform_data = OmniPlatformData(
                platform_status=status.status,
                gemini_model=status.gemini_model,
                total_requests=metrics.total_conversations,
                success_rate=metrics.success_rate,
                avg_response_time=metrics.avg_response_time,
                last_activity=metrics.last_activity,
                error_count=metrics.error_count,
                features=status.features
            )

            logger.info("OMNI platform data updated successfully")

        except Exception as e:
            logger.error(f"Error updating OMNI platform data: {e}")

    async def _restart_service(self, service_name: str) -> bool:
        """Restart a specific service"""
        try:
            # This would implement actual service restart logic
            logger.info(f"Restarting service: {service_name}")
            await asyncio.sleep(2)  # Simulate restart time
            return True
        except Exception as e:
            logger.error(f"Failed to restart service {service_name}: {e}")
            return False

    def start_monitoring(self):
        """Start background monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            monitor_thread.start()
            logger.info("Started operational monitoring")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                self._collect_system_metrics()

                # Check service status
                self._check_services_status()

                # Check cloud resources
                self._check_cloud_resources()

                # Update OMNI platform data
                self._update_omni_platform_data()

                # Generate alerts if needed
                self._generate_alerts()

                # Broadcast real-time data to WebSocket clients
                asyncio.create_task(self._broadcast_websocket_updates())

                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(self.check_interval)

    def _collect_system_metrics(self):
        """Collect current system metrics"""
        try:
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=psutil.cpu_percent(interval=1),
                memory_percent=psutil.virtual_memory().percent,
                disk_usage_percent=psutil.disk_usage('/').percent,
                network_io=dict(psutil.net_io_counters()._asdict()),
                load_average=[x / psutil.cpu_count() * 100 for x in psutil.getloadavg()],
                process_count=len(psutil.pids())
            )

            self.metrics_history.append(metrics)

            # Keep only recent history
            if len(self.metrics_history) > self.max_metrics_history:
                self.metrics_history = self.metrics_history[-self.max_metrics_history:]

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")

    def _check_services_status(self):
        """Check status of all services"""
        services_to_check = [
            "omni-platform", "nginx", "redis-server", "mongodb",
            "postgresql", "docker", "celery", "rabbitmq"
        ]

        for service_name in services_to_check:
            try:
                # Check if service is running
                result = subprocess.run(
                    ["systemctl", "is-active", service_name],
                    capture_output=True, text=True, timeout=5
                )

                if result.returncode == 0:
                    status = ServiceStatus.HEALTHY
                else:
                    status = ServiceStatus.OFFLINE

                # Get service info
                uptime_result = subprocess.run(
                    ["systemctl", "show", service_name, "-p", "ActiveEnterTimestamp"],
                    capture_output=True, text=True, timeout=5
                )

                uptime = None
                if uptime_result.returncode == 0:
                    try:
                        uptime_str = uptime_result.stdout.strip().split('=')[1]
                        uptime = datetime.now() - datetime.fromisoformat(uptime_str.replace('Z', '+00:00'))
                    except:
                        pass

                self.services[service_name] = ServiceInfo(
                    name=service_name,
                    status=status,
                    uptime=uptime,
                    last_check=datetime.now(),
                    response_time=None,
                    error_rate=0.0,
                    version="1.0.0"
                )

            except Exception as e:
                logger.error(f"Failed to check service {service_name}: {e}")
                self.services[service_name] = ServiceInfo(
                    name=service_name,
                    status=ServiceStatus.UNKNOWN,
                    uptime=None,
                    last_check=datetime.now(),
                    response_time=None,
                    error_rate=0.0,
                    version="1.0.0"
                )

    def _check_cloud_resources(self):
        """Check Google Cloud resources"""
        try:
            # Get instance information
            result = subprocess.run(
                ["gcloud", "compute", "instances", "list", "--format=json"],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                instances = json.loads(result.stdout)

                self.cloud_resources = []
                for instance in instances:
                    resource = CloudResource(
                        instance_name=instance["name"],
                        instance_type=instance.get("machineType", "unknown").split('/')[-1],
                        status=instance["status"],
                        external_ip=instance.get("networkInterfaces", [{}])[0].get("accessConfigs", [{}])[0].get("natIP", "none"),
                        zone=instance["zone"].split('/')[-1],
                        cpu_usage=0.0,  # Would need monitoring API
                        memory_usage=0.0,  # Would need monitoring API
                        disk_usage=0.0,  # Would need monitoring API
                        cost_per_hour=self.cost_per_hour.get(instance.get("machineType", "unknown").split('/')[-1], 0.1)
                    )
                    self.cloud_resources.append(resource)

        except Exception as e:
            logger.error(f"Failed to check cloud resources: {e}")

    def _generate_alerts(self):
        """Generate alerts based on current status"""
        current_time = datetime.now()

        # Check for high resource usage
        if self.metrics_history:
            latest = self.metrics_history[-1]

            if latest.cpu_percent > 90:
                self._add_alert("critical", "High CPU usage detected", f"CPU usage at {latest.cpu_percent}%")

            if latest.memory_percent > 90:
                self._add_alert("critical", "High memory usage detected", f"Memory usage at {latest.memory_percent}%")

            if latest.disk_usage_percent > 85:
                self._add_alert("warning", "High disk usage detected", f"Disk usage at {latest.disk_usage_percent}%")

        # Check for offline services
        for service_name, service in self.services.items():
            if service.status == ServiceStatus.OFFLINE:
                self._add_alert("critical", f"Service offline: {service_name}", f"Service {service_name} is not running")

        # Check for cost overruns
        if self.cloud_resources:
            daily_cost = sum(r.cost_per_hour * 24 for r in self.cloud_resources)
            if daily_cost > 10:  # $10/day threshold
                self._add_alert("warning", "High daily cost detected", f"Current daily cost: ${daily_cost:.2f}")

    def _add_alert(self, severity: str, title: str, message: str):
        """Add a new alert"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "title": title,
            "message": message,
            "acknowledged": False
        }

        self.alerts.append(alert)

        # Keep only recent alerts
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]

        logger.warning(f"ALERT [{severity.upper()}]: {title} - {message}")

    async def _broadcast_realtime_data(self, websocket: WebSocket):
        """Broadcast real-time data to a specific WebSocket client"""
        try:
            realtime_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": self._get_metrics_summary(),
                "services": {name: asdict(service) for name, service in self.services.items()},
                "alerts": self.alerts[-5:],  # Last 5 alerts
                "omni_platform": self._get_omni_platform_data() if self.omni_client else None
            }

            await websocket.send_json(realtime_data)

        except Exception as e:
            logger.error(f"Error broadcasting real-time data: {e}")

    async def _broadcast_websocket_updates(self):
        """Broadcast updates to all connected WebSocket clients"""
        if not self.websocket_connections:
            return

        disconnected_clients = []

        for websocket in self.websocket_connections:
            try:
                await self._broadcast_realtime_data(websocket)
            except Exception as e:
                logger.error(f"WebSocket broadcast error: {e}")
                disconnected_clients.append(websocket)

        # Remove disconnected clients
        for websocket in disconnected_clients:
            if websocket in self.websocket_connections:
                self.websocket_connections.remove(websocket)

    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Run the dashboard server"""
        print("Starting OMNI Platform Operational Dashboard...")
        print(f"Dashboard available at: http://{host}:{port}")
        print(f"API endpoints: http://{host}:{port}/api/*")
        print(f"Health check: http://{host}:{port}/api/metrics")

        self.start_monitoring()

        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )

# Main execution
if __name__ == "__main__":
    dashboard = OmniOperationalDashboard()
    dashboard.run()