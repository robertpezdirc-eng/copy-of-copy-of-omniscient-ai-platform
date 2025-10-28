FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    AGENT_MODULE=agent_agentic_ai

WORKDIR /app

COPY agents/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY agents /app/agents

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=10s --start-period=10s --retries=3 \
    CMD ["python","-c","import os,urllib.request,sys; path=os.environ.get('HEALTHCHECK_PATH','/health'); url=f'http://localhost:8000{path}'; r=urllib.request.urlopen(url, timeout=5); sys.exit(0 if getattr(r,'status',200)==200 else 1)"]

CMD ["sh", "-c", "uvicorn agents.${AGENT_MODULE}:app --host 0.0.0.0 --port ${PORT}"]