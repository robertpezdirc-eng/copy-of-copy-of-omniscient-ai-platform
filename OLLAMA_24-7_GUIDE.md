# Ollama 24/7 Monitoring & Auto-Recovery Guide

This guide covers setting up Ollama as a continuously running service with automatic health monitoring, failover, and recovery capabilities.

---

## 🎯 Overview

This setup provides:
1. **24/7 Continuous Integration** - GitHub Actions workflow testing Ollama integration every 4 hours
2. **Ollama as a Daemon Service** - Runs continuously with auto-restart on failure
3. **Automatic Health Monitoring** - Monitors Ollama health and auto-restarts if needed
4. **Automatic Failover** - Backend automatically falls back to LangChain if Ollama fails

---

## 1️⃣ Continuous CI/CD Monitoring

### GitHub Actions Workflow

The workflow `.github/workflows/ollama-monitoring.yml` runs automatically:
- **Schedule**: Every 4 hours
- **On Push**: When backend code or tests change
- **Manual**: Can be triggered manually

**Features**:
- Tests Ollama integration endpoints
- Validates backend imports
- Checks `/api/ai/status` and `/api/health` endpoints
- Notifies on failures

**Manual Trigger**:
```bash
gh workflow run ollama-monitoring.yml
```

**View Results**:
https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/actions

---

## 2️⃣ Ollama as 24/7 Daemon Service

### Quick Setup

```bash
# Option 1: Docker (Recommended - easiest)
./scripts/setup-ollama-24-7.sh docker

# Option 2: Systemd (Linux production servers)
sudo ./scripts/setup-ollama-24-7.sh systemd

# Option 3: Manual setup
./scripts/setup-ollama-24-7.sh manual
```

### Option A: Docker Setup (Recommended)

**Advantages**:
- Cross-platform (Linux, Mac, Windows with WSL)
- Easy to manage
- Built-in health checks
- Auto-restart on failure

**Setup**:
```bash
# Start Ollama service
docker-compose -f docker-compose.ollama.yml up -d

# Check status
docker-compose -f docker-compose.ollama.yml ps

# View logs
docker-compose -f docker-compose.ollama.yml logs -f ollama

# Stop service
docker-compose -f docker-compose.ollama.yml down
```

**Features**:
- Automatic restart if container crashes
- Health checks every 30 seconds
- Separate health monitor container
- Resource limits (4 CPU, 8GB RAM)
- Persistent storage for models

### Option B: Systemd Setup (Linux)

**Advantages**:
- Native Linux integration
- Starts on boot
- System-level process management
- Better for production servers

**Setup**:
```bash
# Install service
sudo ./scripts/setup-ollama-24-7.sh systemd

# Management commands
sudo systemctl status ollama    # Check status
sudo systemctl restart ollama   # Restart
sudo systemctl stop ollama      # Stop
sudo systemctl start ollama     # Start
sudo journalctl -u ollama -f    # View logs
```

**Service File**: `ollama.service`
- Auto-restart with 10-second delay
- Runs as dedicated `ollama` user
- Security hardening enabled
- Watchdog timer (60 seconds)

---

## 3️⃣ Health Check Monitoring

### Automated Health Monitoring

The setup includes a monitoring script that checks Ollama health every 5 minutes and auto-restarts if needed.

**Setup Cron Job**:
```bash
# Edit crontab
crontab -e

# Add this line (checks every 5 minutes)
*/5 * * * * /tmp/ollama-monitor.sh
```

**Manual Health Check**:
```bash
# Check if Ollama is responding
curl http://localhost:11434/api/tags

# Expected output: JSON with list of models
```

### Docker Health Checks

If using Docker, health checks are automatic:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

## 4️⃣ Automatic Failover to LangChain

### How It Works

The backend (`backend/main.py`) implements automatic failover:

```python
@app.post("/api/ai/generate")
def ai_generate(body: AIGenerateBody):
    """Tries Ollama first if enabled, falls back to LangChain providers."""
    if USE_OLLAMA:
        try:
            # Attempt Ollama generation
            return ollama_response
        except Exception:
            pass  # Fall through to LangChain
    
    # Fallback to LangChain providers
    return langchain_response
```

**Fallback Scenarios**:
1. Ollama service is down
2. Ollama request times out
3. Ollama returns an error
4. Model not loaded

**No Manual Intervention Required** - Failover is automatic!

### Check Current Provider

```bash
# Check which AI providers are available
curl http://localhost:8000/api/ai/status

# Response shows:
# - ollama.enabled
# - ollama.available
# - langchain.available
```

---

## 📊 Monitoring Dashboard

### Checking System Health

**1. Backend Health**:
```bash
curl http://localhost:8000/api/health
# Expected: {"status": "ok"}
```

**2. AI Provider Status**:
```bash
curl http://localhost:8000/api/ai/status
# Shows Ollama and LangChain availability
```

**3. Ollama Directly**:
```bash
curl http://localhost:11434/api/tags
# Lists available models
```

### Log Locations

| Service | Log Location |
|---------|-------------|
| **Ollama (systemd)** | `sudo journalctl -u ollama -f` |
| **Ollama (Docker)** | `docker logs ollama-service -f` |
| **Health Monitor** | `/var/log/ollama-monitor.log` |
| **Backend** | Application logs |
| **GitHub Actions** | https://github.com/.../actions |

---

## 🔧 Troubleshooting

### Ollama Not Starting

**Docker**:
```bash
# Check container status
docker ps -a | grep ollama

# View logs
docker logs ollama-service

# Restart
docker restart ollama-service
```

**Systemd**:
```bash
# Check service status
sudo systemctl status ollama

# View recent logs
sudo journalctl -u ollama -n 50

# Restart
sudo systemctl restart ollama
```

### Ollama Running but Not Responding

```bash
# Check if port is accessible
curl -v http://localhost:11434/api/tags

# Check process
ps aux | grep ollama

# Check resource usage
docker stats ollama-service  # For Docker
# or
top -p $(pgrep ollama)      # For systemd
```

### Models Not Loading

```bash
# Pull model manually
ollama pull qwen3-coder:30b

# List available models
ollama list

# Check model size and disk space
df -h
du -sh ~/.ollama/models  # or /var/lib/ollama/models
```

### Automatic Failover Not Working

1. **Check backend logs** for errors
2. **Verify LangChain providers** are configured:
   ```bash
   echo $OPENAI_API_KEY  # Should be set
   ```
3. **Test endpoints directly**:
   ```bash
   curl -X POST http://localhost:8000/api/ai/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello"}'
   ```

---

## 🚀 Production Deployment

### Recommended Setup for Production

1. **Use Docker Compose** for consistency:
   ```bash
   docker-compose -f docker-compose.ollama.yml up -d
   ```

2. **Enable monitoring cron job**:
   ```bash
   crontab -e
   # Add: */5 * * * * /tmp/ollama-monitor.sh
   ```

3. **Configure backend environment**:
   ```bash
   export USE_OLLAMA=true
   export OLLAMA_URL=http://localhost:11434
   export OPENAI_API_KEY=your-fallback-key  # For failover
   ```

4. **Set up GitHub Actions monitoring**:
   - Workflow automatically monitors integration
   - Get notifications on failures
   - Runs every 4 hours

### Resource Requirements

| Component | CPU | RAM | Disk |
|-----------|-----|-----|------|
| **Ollama Service** | 2-4 cores | 4-8 GB | 20+ GB |
| **Model (qwen3:30b)** | - | - | ~17 GB |
| **Model (llama2)** | - | - | ~3.8 GB |
| **Backend** | 1 core | 512 MB | 1 GB |

---

## 📈 Performance Tuning

### Docker Resource Limits

Edit `docker-compose.ollama.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '8'      # Increase for better performance
      memory: 16G    # Increase for larger models
    reservations:
      cpus: '4'
      memory: 8G
```

### Systemd Resource Limits

Edit `ollama.service`:
```ini
[Service]
LimitNOFILE=1048576   # Max open files
LimitNPROC=1024       # Max processes
CPUQuota=400%         # 4 CPU cores
MemoryLimit=8G        # 8GB RAM
```

---

## 📝 Configuration Files

| File | Purpose |
|------|---------|
| `.github/workflows/ollama-monitoring.yml` | CI/CD monitoring workflow |
| `docker-compose.ollama.yml` | Docker service configuration |
| `ollama.service` | Systemd service configuration |
| `scripts/setup-ollama-24-7.sh` | Automated setup script |
| `/tmp/ollama-monitor.sh` | Health monitoring script |

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Ollama service is running
  ```bash
  curl http://localhost:11434/api/tags
  ```

- [ ] Auto-restart is configured
  ```bash
  # For Docker: stop and check if it restarts
  docker stop ollama-service && sleep 5 && docker ps | grep ollama
  
  # For systemd: check restart policy
  systemctl show ollama | grep Restart
  ```

- [ ] Backend can connect to Ollama
  ```bash
  curl http://localhost:8000/api/ai/status
  ```

- [ ] Automatic failover works
  ```bash
  # Stop Ollama temporarily
  docker stop ollama-service  # or: sudo systemctl stop ollama
  
  # Test backend - should fall back to LangChain
  curl -X POST http://localhost:8000/api/ai/generate \
    -H "Content-Type: application/json" \
    -d '{"prompt": "test"}'
  
  # Restart Ollama
  docker start ollama-service  # or: sudo systemctl start ollama
  ```

- [ ] GitHub Actions workflow is active
  - Check: https://github.com/robertpezdirc-eng/copy-of-copy-of-omniscient-ai-platform/actions

- [ ] Health monitoring cron is set
  ```bash
  crontab -l | grep ollama-monitor
  ```

---

## 🆘 Support

### Common Issues

1. **"Connection refused" error**
   - Ollama not running: Start service
   - Wrong port: Check OLLAMA_URL setting
   - Firewall: Open port 11434

2. **"Model not found" error**
   - Pull model: `ollama pull model-name`
   - Check models: `ollama list`

3. **High memory usage**
   - Normal for large models (30B uses ~17GB)
   - Use smaller models if limited RAM
   - Adjust Docker memory limits

4. **Slow responses**
   - Increase CPU allocation
   - Use GPU-enabled Ollama
   - Try smaller models

### Getting Help

- Check logs (see Log Locations above)
- Review GitHub Actions failures
- Test each component individually
- Verify network connectivity

---

## 📚 Additional Resources

- [Ollama Documentation](https://ollama.ai/docs)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Systemd Documentation](https://systemd.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [OLLAMA_CICD_GUIDE.md](./OLLAMA_CICD_GUIDE.md) - Original integration guide

---

**Status**: ✅ All components implemented and ready for 24/7 operation!
