# 🌐 OMNI Learning Overlay

## 📋 Overview

The OMNI Learning Overlay is a background learning system that connects with your existing OMNI Core to provide continuous agent learning using ChatGPT and Gemini AI services.

## ✨ Features

### 🤖 Background Learning
- **Continuous learning** - Agents learn every hour automatically
- **Multi-AI integration** - Uses ChatGPT, Gemini, and OMNI AI
- **Non-intrusive** - Doesn't interfere with main Core operations
- **Memory management** - Saves all learned knowledge

### 📊 Analytics & Monitoring
- **Learning statistics** - Track agent progress and knowledge
- **Memory analysis** - View what agents have learned
- **Progress tracking** - Monitor learning over time
- **API endpoints** - Access learning data programmatically

### 🔗 Core Integration
- **Connects with existing agents** - Uses your current OMNI setup
- **API compatibility** - Works with existing OMNI endpoints
- **Configuration management** - Easy setup and customization
- **Error handling** - Graceful fallbacks when APIs unavailable

## 🚀 Quick Start

### 1. Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Or manually
pip install requests python-dotenv
```

### 2. Configuration
Edit `overlay_config.json`:
```json
{
  "learning_interval": 3600,
  "agents_to_learn": ["learning", "commercial", "optimization"],
  "learning_topics": [
    "samoizboljševanje znanja",
    "napredne AI tehnike",
    "sistemska optimizacija"
  ]
}
```

### 3. Start Learning
```bash
# Start the learning overlay
python launch_overlay.py

# Or run background learning directly
python background_learning.py
```

## 📁 Project Structure

```
omni_learning_overlay/
├── background_learning.py      # Main learning loop
├── analytics.py                # Analytics and statistics
├── omni_core_api.py           # Connection to OMNI Core
├── overlay_config.json         # Configuration settings
├── requirements.txt           # Python dependencies
├── launch_overlay.py          # Launcher script
└── memory/                    # Agent knowledge storage
    ├── learning.json
    ├── commercial.json
    └── optimization.json
```

## 🔧 Configuration Options

### overlay_config.json
```json
{
  "learning_interval": 3600,           // Learning cycle in seconds
  "agents_to_learn": ["learning", "commercial", "optimization"],
  "learning_topics": [                 // Topics for learning
    "samoizboljševanje znanja",
    "napredne AI tehnike",
    "sistemska optimizacija"
  ],
  "ai_providers": ["openai", "gemini", "omni"],
  "memory_retention_days": 30,         // Keep memory for 30 days
  "enable_background_learning": true,
  "enable_analytics_api": true,
  "omni_core_api_url": "http://localhost:3001/api"
}
```

## 🎯 Usage Examples

### Start Background Learning
```python
from background_learning import OmniLearningOverlay

overlay = OmniLearningOverlay()
overlay.run_background_learning()
```

### Get Learning Analytics
```python
from analytics import get_all_agents_memory, get_learning_progress

# Get all agents' memory
all_memory = get_all_agents_memory()
print(f"Total topics learned: {all_memory['total_learned_topics']}")

# Get learning progress for last 7 days
progress = get_learning_progress(7)
print(f"Topics in last 7 days: {progress['total_learned']}")
```

### Connect with OMNI Core
```python
from omni_core_api import get_all_agents, ask_agent_ai

# Get agents from Core
agents = get_all_agents()
print(f"Available agents: {agents}")

# Ask agent a question
response = ask_agent_ai("learning", "Kako se lahko izboljšam?")
print(f"Agent response: {response}")
```

## 🔌 API Integration

### OMNI Search Integration
The learning overlay integrates with the OMNI Search interface:

1. **Learning data display** - Shows learning statistics in search interface
2. **Real-time updates** - Live learning progress tracking
3. **Agent memory access** - Query what agents have learned
4. **Background operation** - Silent learning without UI interference

### API Endpoints (via OMNI Search server)
- `GET /api/learning/status` - Current learning status
- `GET /api/learning/analytics` - Detailed analytics
- `GET /api/health` - System health check

## 📊 Monitoring

### Check Learning Status
```bash
# View learning logs
tail -f omni_learning_overlay/learning.log

# Check memory files
ls -la omni_learning_overlay/memory/

# View specific agent memory
cat omni_learning_overlay/memory/learning.json
```

### Analytics Data
The system tracks:
- **Topics learned** per agent
- **Learning frequency** and patterns
- **Memory usage** and retention
- **API connectivity** status
- **Error rates** and recovery

## 🔧 Troubleshooting

### Common Issues

**1. OMNI Core not accessible**
```
Error: Connection to OMNI Core failed
Solution: Ensure OMNI server is running on port 3001
```

**2. API keys not configured**
```
Warning: OpenAI API key not configured
Solution: Set OPENAI_API_KEY environment variable
```

**3. Memory folder not created**
```
Error: Memory folder not found
Solution: Run background_learning.py first to create folders
```

### Debug Mode
Enable debug logging by setting:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## 🚀 Advanced Features

### Custom Learning Topics
Add specific topics for each agent in `overlay_config.json`:
```json
{
  "agent_specific_topics": {
    "learning": ["machine learning", "neural networks", "deep learning"],
    "commercial": ["digital marketing", "sales strategies", "customer analytics"],
    "optimization": ["performance tuning", "resource optimization", "scalability"]
  }
}
```

### Scheduled Learning
Modify learning intervals per agent:
```json
{
  "learning_schedule": {
    "learning": 1800,      // Every 30 minutes
    "commercial": 7200,    // Every 2 hours
    "optimization": 3600   // Every hour
  }
}
```

## 📈 Performance

### Optimization Tips
- **Memory cleanup** - Run `cleanup_old_memory()` regularly
- **Batch learning** - Process multiple topics together
- **Error recovery** - Automatic retry on API failures
- **Resource monitoring** - Track system resource usage

### Scaling
- **Multiple instances** - Run on different machines
- **Load balancing** - Distribute learning across servers
- **Database storage** - Move memory to persistent storage
- **API rate limiting** - Respect AI service limits

## 🔐 Security

### API Key Management
- Store keys in environment variables
- Never commit keys to version control
- Use secure key rotation
- Monitor API usage and costs

### Access Control
- Restrict learning overlay access
- Monitor learning activities
- Audit learning sessions
- Secure memory storage

## 📞 Support

The OMNI Learning Overlay integrates seamlessly with:
- **Existing OMNI Core** agents and APIs
- **OMNI Search** interface for monitoring
- **External AI services** (ChatGPT, Gemini)
- **Custom integrations** via API endpoints

---

**🌐 Part of the OMNI AI Ecosystem**
**Built for seamless integration with existing OMNI infrastructure**