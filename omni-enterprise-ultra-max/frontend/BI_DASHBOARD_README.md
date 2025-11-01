# BI Dashboard - Business Intelligence & Analytics

## Overview

The BI Dashboard provides comprehensive real-time monitoring and analytics for AI/ML services with advanced visualizations using D3.js and Recharts.

## Features

### 1. Real-Time Metrics (`/bi-dashboard`)
- **Live WebSocket Connection**: Real-time data streaming from backend services
- **System Metrics**: CPU usage, memory consumption, request rates, latency
- **Trend Analysis**: Automatic calculation of performance trends
- **Interactive Charts**: Area charts for CPU/Memory, line charts for requests/latency

### 2. D3.js Visualizations

#### TreeMap - Service Usage Distribution
- Visual representation of AI service usage by request volume
- Hierarchical display showing relative popularity
- Color-coded by service category

#### Force Graph - Service Dependencies
- Interactive network diagram of microservice relationships
- Draggable nodes for exploration
- Edge thickness indicates connection strength
- Colored by service layer (API Gateway, AI Services, Data Layer)

#### HeatMap - Model Performance Over Time
- Time-series performance visualization
- Color intensity represents model accuracy
- Quick identification of performance patterns and anomalies

### 3. Model Performance Cards
Real-time summary cards for each AI model:
- **LSTM Revenue Forecasting**
- **Anomaly Detection**
- **Hybrid Recommendations**
- **Swarm Optimizer**
- **AGI Framework**

Each card displays:
- Current accuracy percentage
- Average latency (ms)
- Request count

## Installation

### 1. Install Dependencies

```bash
cd frontend
npm install
```

New dependencies added:
- `d3@^7.8.5` - D3.js for advanced visualizations
- `@types/d3@^7.4.3` - TypeScript definitions
- `socket.io-client@^4.7.2` - WebSocket client for real-time data

### 2. Environment Configuration

Create `.env` file in `frontend/` directory:

```bash
# WebSocket connection for real-time metrics
VITE_WS_URL=ws://localhost:8080

# API endpoint (if different from WebSocket)
VITE_API_URL=http://localhost:8080
```

For production (Cloud Run):
```bash
VITE_WS_URL=wss://omni-ai-worker-661612368188.europe-west1.run.app
VITE_API_URL=https://omni-ai-worker-661612368188.europe-west1.run.app
```

### 3. Run Development Server

```bash
npm run dev
```

Navigate to: `http://localhost:5173/bi-dashboard`

## Components Architecture

```
src/
├── pages/
│   └── BIDashboard.tsx          # Main dashboard page with tabs
├── components/
│   └── dashboard/
│       ├── RealTimeMetrics.tsx   # Live metrics with Recharts
│       └── D3Visualizations.tsx  # D3.js TreeMap, ForceGraph, HeatMap
└── hooks/
    └── useWebSocket.ts           # WebSocket connection hook
```

## WebSocket Events

The dashboard listens for these real-time events:

```typescript
// Metrics update event
socket.on('metrics:update', (data: MetricData) => {
  // data = { timestamp, cpu, memory, requests, latency }
});

// Connection events
socket.on('connect', () => { /* Connected */ });
socket.on('disconnect', () => { /* Disconnected */ });
socket.on('connect_error', (err) => { /* Handle error */ });
```

## Backend Integration

### WebSocket Server (ai-worker)

The backend should emit metrics updates periodically:

```python
# In ai-worker/main.py or websocket_routes.py

from fastapi import WebSocket
import asyncio
import psutil
from datetime import datetime

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Collect metrics
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu": psutil.cpu_percent(),
                "memory": psutil.virtual_memory().percent,
                "requests": get_request_count(),  # Implement counter
                "latency": get_avg_latency()      # Implement calculator
            }
            
            # Send to client
            await websocket.send_json({
                "event": "metrics:update",
                "data": metrics
            })
            
            await asyncio.sleep(2)  # Update every 2 seconds
            
    except WebSocketDisconnect:
        print("Client disconnected")
```

### REST API Endpoints

```python
# Model performance endpoint
@app.get("/api/analytics/model-performance")
async def get_model_performance():
    return [
        {
            "name": "LSTM Revenue",
            "accuracy": 94.2,
            "latency": 45,
            "requests": 1250
        },
        # ... more models
    ]
```

## Customization

### Adding New Visualizations

1. Create component in `src/components/dashboard/`:

```typescript
import { useRef, useEffect } from 'react';
import * as d3 from 'd3';

export const MyCustomD3Chart = ({ data }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  
  useEffect(() => {
    if (!svgRef.current) return;
    
    const svg = d3.select(svgRef.current);
    // ... D3 visualization code
    
  }, [data]);
  
  return <svg ref={svgRef}></svg>;
};
```

2. Add to `BIDashboard.tsx`:

```typescript
// Add tab state
const [activeTab, setActiveTab] = useState<'realtime' | 'custom'>('realtime');

// Add tab button
<button onClick={() => setActiveTab('custom')}>
  Custom Chart
</button>

// Add content
{activeTab === 'custom' && <MyCustomD3Chart data={myData} />}
```

### Styling

All components use Tailwind CSS utility classes. Modify colors/spacing in component files:

```typescript
// Example: Change metric card color
<div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
  {/* Change border-green-500 to any color */}
</div>
```

## Performance Considerations

1. **WebSocket Connection**:
   - Single connection shared across components
   - Automatic reconnection with exponential backoff
   - Connection pooling in production

2. **Chart Rendering**:
   - D3 charts render only on data changes
   - Limited data points (last 20 for real-time metrics)
   - Debounced updates for smooth animations

3. **Memory Management**:
   - Cleanup listeners on component unmount
   - Remove D3 elements before re-render
   - Limit historical data storage

## Troubleshooting

### WebSocket Not Connecting

1. Check VITE_WS_URL in `.env`
2. Ensure backend WebSocket endpoint is running
3. Check browser console for connection errors
4. Verify CORS settings allow WebSocket upgrade

### Charts Not Rendering

1. Verify data format matches component props
2. Check browser console for D3 errors
3. Ensure SVG ref is properly attached
4. Confirm viewport size is adequate (width/height > 0)

### Dependencies Installation Issues

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Or use npm ci for clean install
npm ci
```

## Production Deployment

### Build for Production

```bash
npm run build
```

This creates optimized bundle in `dist/` directory.

### Environment Variables (Cloud Run)

Set in `cloudbuild-frontend.yaml` or Cloud Run console:

```yaml
env:
  - name: VITE_WS_URL
    value: wss://omni-ai-worker-661612368188.europe-west1.run.app
  - name: VITE_API_URL
    value: https://omni-ai-worker-661612368188.europe-west1.run.app
```

### Nginx Configuration

Ensure WebSocket upgrade in `nginx.conf`:

```nginx
location /ws/ {
    proxy_pass http://backend:8080;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

## Future Enhancements

- [ ] Real-time alerts and notifications
- [ ] Custom dashboard layouts (drag-and-drop)
- [ ] Export charts as PNG/SVG
- [ ] Historical data playback
- [ ] Multi-tenant filtering
- [ ] Predictive analytics overlay
- [ ] A/B test comparison views
- [ ] Anomaly highlighting in visualizations

## Tech Stack

- **React 18.2**: UI framework
- **TypeScript 5.2**: Type safety
- **D3.js 7.8**: Advanced visualizations
- **Recharts 2.10**: Declarative charts
- **Socket.IO Client 4.7**: WebSocket client
- **Tailwind CSS**: Utility-first styling
- **Lucide React**: Icon library
- **Vite 5.0**: Build tool

## License

Part of Omni Enterprise Ultra Max platform.
