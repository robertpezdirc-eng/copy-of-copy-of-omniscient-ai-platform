import os
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import (
    CollectorRegistry,
    CONTENT_TYPE_LATEST,
    generate_latest,
    Gauge,
    Counter,
    Histogram,
)
import requests
from pydantic import BaseModel

try:
    # Optional: LangChain providers
    from .llm_langchain import invoke_llm
except Exception:
    invoke_llm = None

try:
    import stripe as _stripe  # optional
except Exception:
    _stripe = None


app = FastAPI(title="Omni Cloud Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return JSONResponse({"status": "ok"})


@app.get("/api/v1/omni/summary")
def omni_summary():
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    # Privzete demo vrednosti
    revenue = 23450.0
    uptime = 99.98
    active_users = 184
    requests_total = 3200

    # 1) Stripe (če je na voljo STRIPE_API_KEY)
    api_key = os.getenv("STRIPE_API_KEY")
    if api_key and _stripe is not None:
        try:
            _stripe.api_key = api_key
            # Seštej uspešne charge zadnjih 24h (demo logika)
            since = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
            charges = _stripe.Charge.list(limit=100, created={"gte": since})
            total = 0
            for ch in charges.auto_paging_iter():
                if getattr(ch, "paid", False) and getattr(ch, "status", "") == "succeeded":
                    total += getattr(ch, "amount", 0) / 100.0
            if total > 0:
                revenue = round(total, 2)
        except Exception:
            # Če zatajimo, ostanemo pri demo vrednosti
            pass

    # 2) Prometheus (če je na voljo PROMETHEUS_SUM_REQUESTS_URL)
    prom_url = os.getenv("PROMETHEUS_SUM_REQUESTS_URL")
    if prom_url:
        try:
            r = requests.get(prom_url, timeout=5)
            if r.ok:
                data = r.json()
                # pričakovan format: data.result[0].value[1]
                value = float(data["data"]["result"][0]["value"][1])
                requests_total = int(value)
        except Exception:
            pass

    payload = {
        "time": now,
        "revenue": revenue,
        "uptime": uptime,
        "active_users": active_users,
        "requests": requests_total,
    }
    return JSONResponse(payload)


# Preprost /metrics z runtime metrikami, prilagojeno za Cloud Run
_registry = CollectorRegistry()
_g_uptime = Gauge("omni_uptime_percent", "Service uptime percentage", registry=_registry)
_g_active_users = Gauge("omni_active_users", "Number of active users", registry=_registry)
_g_requests = Gauge("omni_requests_total", "Total requests (demo)", registry=_registry)
_g_revenue = Gauge("omni_revenue", "Revenue (demo currency units)", registry=_registry)

# Ollama metrics
_c_ollama_requests = Counter(
    "omni_ollama_requests_total",
    "Total Ollama requests",
    labelnames=("endpoint", "model"),
    registry=_registry,
)
_c_ollama_errors = Counter(
    "omni_ollama_errors_total",
    "Total Ollama errors",
    labelnames=("endpoint", "model"),
    registry=_registry,
)
_h_ollama_latency = Histogram(
    "omni_ollama_request_duration_seconds",
    "Ollama request duration in seconds",
    labelnames=("endpoint", "model"),
    buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 30, 60),
    registry=_registry,
)
_c_ollama_eval_tokens = Counter(
    "omni_ollama_eval_tokens_total",
    "Total evaluated tokens reported by Ollama",
    labelnames=("endpoint", "model"),
    registry=_registry,
)
_c_ollama_prompt_tokens = Counter(
    "omni_ollama_prompt_tokens_total",
    "Total prompt tokens reported by Ollama",
    labelnames=("endpoint", "model"),
    registry=_registry,
)


@app.get("/metrics")
def metrics():
    # Uskladi z istimi vrednostmi kot summary (demo)
    _g_uptime.set(99.98)
    _g_active_users.set(184)
    _g_requests.set(3200)
    _g_revenue.set(23450)
    data = generate_latest(_registry)
    return PlainTextResponse(data.decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


# ==============================
# Ollama integration (local API)
# ==============================

def _ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def _ollama_default_model() -> str:
    # Privzeto uporabljamo Qwen3 Coder 30B (usklajeno z lokalno namestitvijo)
    return os.getenv("OLLAMA_MODEL", "qwen3-coder:30b")


def _ollama_timeout_seconds() -> int:
    try:
        return int(os.getenv("OLLAMA_TIMEOUT_SEC", "300"))
    except Exception:
        return 300


@app.get("/api/ollama/models")
def list_ollama_models():
    base = _ollama_base_url()
    try:
        r = requests.get(f"{base}/api/tags", timeout=10)
        r.raise_for_status()
        return JSONResponse(r.json())
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=502)


@app.get("/api/ollama/health")
def ollama_health():
    base = _ollama_base_url()
    try:
        r = requests.get(base, timeout=5)
        ok = r.ok
        return JSONResponse({"base": base, "ok": ok, "status_code": r.status_code})
    except Exception as e:
        return JSONResponse({"base": base, "ok": False, "error": str(e)}, status_code=502)


@app.post("/api/ollama/generate")
def ollama_generate(payload: dict):
    base = _ollama_base_url()
    model = payload.get("model") or _ollama_default_model()
    prompt = payload.get("prompt") or ""
    options = payload.get("options") or {}
    stream = bool(payload.get("stream", False))

    labels = {"endpoint": "generate", "model": model}
    _c_ollama_requests.labels(**labels).inc()
    with _h_ollama_latency.labels(**labels).time():
        try:
            r = requests.post(
                f"{base}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": stream,
                    "options": options,
                    # Podpri keep_alive, če je poslan v payload (da ostane model v RAM-u)
                    **({"keep_alive": payload.get("keep_alive")} if payload.get("keep_alive") is not None else {}),
                },
                timeout=_ollama_timeout_seconds(),
            )
            r.raise_for_status()
            data = r.json()
            # Token telemetry, if available
            if isinstance(data, dict):
                eval_cnt = data.get("eval_count")
                if isinstance(eval_cnt, int):
                    _c_ollama_eval_tokens.labels(**labels).inc(eval_cnt)
                p_cnt = data.get("prompt_eval_count")
                if isinstance(p_cnt, int):
                    _c_ollama_prompt_tokens.labels(**labels).inc(p_cnt)
            return JSONResponse({"model": model, **data})
        except Exception as e:
            _c_ollama_errors.labels(**labels).inc()
            return JSONResponse({"error": str(e), "model": model}, status_code=502)


@app.post("/api/ollama/chat")
def ollama_chat(payload: dict):
    base = _ollama_base_url()
    model = payload.get("model") or _ollama_default_model()
    messages = payload.get("messages") or []
    options = payload.get("options") or {}
    stream = bool(payload.get("stream", False))

    labels = {"endpoint": "chat", "model": model}
    _c_ollama_requests.labels(**labels).inc()
    with _h_ollama_latency.labels(**labels).time():
        try:
            r = requests.post(
                f"{base}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": stream,
                    "options": options,
                    **({"keep_alive": payload.get("keep_alive")} if payload.get("keep_alive") is not None else {}),
                },
                timeout=_ollama_timeout_seconds(),
            )
            r.raise_for_status()
            data = r.json()
            # Token telemetry (if available, some builds return usage-like fields)
            if isinstance(data, dict):
                usage = data.get("usage") or {}
                p_cnt = usage.get("prompt_tokens") or data.get("prompt_eval_count")
                c_cnt = usage.get("completion_tokens") or data.get("eval_count")
                if isinstance(p_cnt, int):
                    _c_ollama_prompt_tokens.labels(**labels).inc(p_cnt)
                if isinstance(c_cnt, int):
                    _c_ollama_eval_tokens.labels(**labels).inc(c_cnt)
            return JSONResponse({"model": model, **data})
        except Exception as e:
            _c_ollama_errors.labels(**labels).inc()
            return JSONResponse({"error": str(e), "model": model}, status_code=502)


# ==============================
# LangChain unified endpoint
# ==============================

class LCGenerateBody(BaseModel):
    provider: str
    model: str
    prompt: str
    temperature: float | None = None
    max_tokens: int | None = None
    # Vertex optional extras
    project: str | None = None
    location: str | None = None


@app.post("/api/langchain/generate")
def langchain_generate(body: LCGenerateBody):
    if invoke_llm is None:
        return JSONResponse({"error": "LangChain not available on server"}, status_code=501)
    try:
        text = invoke_llm(
            provider=body.provider,
            model=body.model,
            prompt=body.prompt,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            project=body.project,
            location=body.location,
        )
        return JSONResponse({
            "provider": body.provider,
            "model": body.model,
            "response": text,
        })
    except ValueError as e:
        # Input validation errors (e.g., invalid API key encoding)
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=502)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)