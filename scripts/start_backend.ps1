$ErrorActionPreference = 'Stop'
$Env:OLLAMA_TIMEOUT_SEC = '420'
uvicorn backend.main:app --host 0.0.0.0 --port 8082 --log-level info