# OMNI Unified Platform - Cloud Run container (FastAPI + Uvicorn)
# Združuje vse OMNI komponente z Vertex AI integracijo
FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV GOOGLE_CLOUD_PROJECT=refined-graph-471712-n9
ENV GOOGLE_CLOUD_REGION=europe-west1
ENV VERTEX_AI_MODEL=gemini-2.5-pro
ENV VERTEX_AI_API_KEY=AQ.Ab8RN6LjDXj9_BHBcp-XvbSm0WCE2ftjfwyobHz-Zc3oNMVfhQ
ENV PORT=8080

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements_unified.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY omni_unified_platform.py .
COPY vertex_ai_config.json .

# Copy all files (Docker will handle missing directories gracefully)
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

EXPOSE 8080

# Health check (extended start-period for Cloud Run)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the unified platform
CMD ["python", "omni_unified_platform.py"]