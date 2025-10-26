# 🌐 OMNI Real-Time Chat System

Autonomous AI chat system with real-time platform responses.

## Features

- **Real-Time Responses**: Autonomous OMNI Director provides live platform data
- **No Pre-scripted Responses**: All answers are based on current platform state
- **Multi-Agent System**: 8 active agents providing different capabilities
- **Modern UI**: React frontend with Tailwind CSS styling
- **RESTful API**: Flask backend with CORS support

## Architecture

### Backend (Python/Flask)
- **Port**: 8080
- **Framework**: Flask with CORS
- **AI Director**: Autonomous response system
- **Real-Time Data**: Live platform metrics

### Frontend (React/Tailwind)
- **Port**: 3000 (React dev server)
- **Styling**: Custom dark theme with neon accents
- **Responsive**: Mobile-friendly design
- **Real-Time**: Live chat updates

## Installation & Setup

### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the Flask API server
python chat_api.py
```

### 2. Frontend Setup

```bash
# Install Node.js dependencies
npm install

# Start the React development server
npm start
```

## Usage

### Starting the System

1. **Start Backend API**:
   ```bash
   python chat_api.py
   ```
   - API will be available at http://localhost:8080

2. **Start Frontend**:
   ```bash
   npm start
   ```
   - React app will be available at http://localhost:3000

### Chat Commands

The OMNI Director responds to various queries in real-time:

- **"status"** - Get current platform status
- **"agents"** - View active agents
- **"capabilities"** - See platform features
- **"help"** - Get help information
- **General questions** - Receive contextual responses

## API Endpoints

### POST /api/chat
Send a message to the OMNI Director

**Request:**
```json
{
  "message": "What is the current platform status?"
}
```

**Response:**
```json
{
  "reply": "🟢 OMNI Platform Status (Real-Time)\n⏰ Time: 14:30:25\n\n📊 System Health: 98%\n🤖 Active Agents: 8/8...",
  "status": "success",
  "timestamp": "2024-01-15T14:30:25.123Z",
  "metadata": {
    "query_type": "system_status",
    "platform_status": {...}
  }
}
```

### GET /api/health
Check API health status

### GET /api/agents
Get real-time agent information

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true

# OMNI Platform Settings
OMNI_PLATFORM_URL=http://localhost:3001
OMNI_API_KEY=your_api_key_here
```

## Development

### Project Structure

```
omni-search/
├── chat_api.py          # Flask backend API
├── requirements.txt     # Python dependencies
├── package.json         # Node.js dependencies
├── tailwind.config.js   # Tailwind CSS config
├── src/
│   ├── App.js          # Main React component
│   ├── OmniRealChat.js # Chat interface
│   ├── index.js        # React entry point
│   └── index.css       # Global styles
└── public/
    ├── index.html      # HTML template
    └── manifest.json   # PWA manifest
```

### Adding New Features

1. **New Chat Commands**: Add methods to `OmniDirector` class
2. **UI Enhancements**: Modify `OmniRealChat.js` component
3. **API Endpoints**: Add new routes to `chat_api.py`

## Troubleshooting

### Common Issues

1. **Port Conflicts**:
   - Backend uses port 8080
   - Frontend uses port 3000
   - Node.js server uses port 3001

2. **CORS Issues**:
   - Flask-CORS is enabled for all routes
   - Check browser console for errors

3. **API Connection**:
   - Ensure backend is running before frontend
   - Check network connectivity

### Debug Mode

Enable debug logging:

```python
# In chat_api.py
app.run(host='0.0.0.0', port=8080, debug=True)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the OMNI Platform ecosystem.

---

**Built with ❤️ for the OMNI Platform**