import os, logging, requests
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    GENAI_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omni_hybrid_ai")

class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.endpoint = os.getenv("OPENAI_CHAT_ENDPOINT", "https://api.openai.com/v1/chat/completions")
    def chat(self, prompt: str) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("Missing OPENAI_API_KEY")
        h = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        b = {"model": self.model, "messages": [{"role":"system","content":"You are a helpful assistant."},{"role":"user","content":prompt}], "temperature": float(os.getenv("OPENAI_TEMPERATURE","0.7"))}
        r = requests.post(self.endpoint, headers=h, json=b, timeout=60)
        if r.status_code >= 400:
            raise RuntimeError(f"OpenAI error {r.status_code}: {r.text}")
        d = r.json(); t = d.get("choices", [{}])[0].get("message", {}).get("content")
        logger.info(f"provider=openai model={self.model} len={len(t or '')}")
        return {"provider":"openai","model":self.model,"text":t,"raw":d}

class GeminiClient:
    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or os.getenv("VERTEX_AI_MODEL", "gemini-2.5-flash-preview-09-2025")
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    def generate(self, prompt: str) -> Dict[str, Any]:
        if not GENAI_AVAILABLE or not self.api_key:
            raise RuntimeError("Gemini API not available or missing key")
        genai.configure(api_key=self.api_key)
        m = genai.GenerativeModel(self.model)
        r = m.generate_content(prompt)
        t = getattr(r, "text", None) or str(r)
        logger.info(f"provider=gemini model={self.model} len={len(t or '')}")
        return {"provider":"gemini","model":self.model,"text":t,"raw":getattr(r,"to_dict",lambda: str(r))()}

class OmniRouter:
    def __init__(self, openai_client: OpenAIClient, gemini_client: GeminiClient):
        self.openai = openai_client; self.gemini = gemini_client
    def route(self, prompt: str, provider: Optional[str] = None) -> Dict[str, Any]:
        p = prompt.lower()
        gemini_available = GENAI_AVAILABLE and bool(self.gemini.api_key)
        # Force provider if explicitly requested
        if provider:
            pv = provider.strip().lower()
            if pv in ("gemini","vertex"):
                if gemini_available:
                    try:
                        return self.gemini.generate(prompt)
                    except Exception as e:
                        logger.warning(f"Gemini route failed, falling back to OpenAI: {e}")
                        return self.openai.chat(prompt)
                else:
                    logger.info("Gemini requested but unavailable; falling back to OpenAI")
                    return self.openai.chat(prompt)
            elif pv in ("openai","oai"):
                return self.openai.chat(prompt)
            else:
                logger.info(f"Unknown provider '{provider}', defaulting to heuristic")
        # Heuristic routing
        gemini_keywords = ["podatki","google","dogodek","lokacija","vijesti","info"]
        openai_keywords = ["ustvari","pesma","koda","ideja","analiza","napravi"]
        if any(w in p for w in gemini_keywords) and gemini_available:
            try:
                return self.gemini.generate(prompt)
            except Exception as e:
                logger.warning(f"Gemini route failed, falling back to OpenAI: {e}")
                return self.openai.chat(prompt)
        elif any(w in p for w in openai_keywords):
            return self.openai.chat(prompt)
        # Default fallback: OpenAI
        return self.openai.chat(prompt)

app = FastAPI(title="OMNI Hybrid AI", version="1.0.0")
origins_env = os.getenv("OMNI_ALLOWED_ORIGINS", "*").strip()
if not origins_env or origins_env == "*":
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    origins = [o.strip() for o in origins_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

_openai = OpenAIClient(); _gemini = GeminiClient(); _router = OmniRouter(_openai, _gemini)

@app.get("/health")
async def health():
    return {"status":"ok","service":"omni-hybrid-ai"}

@app.get("/health/providers")
async def health_providers():
    return {
        "openai": bool(_openai.api_key),
        "gemini": bool(_gemini.api_key) and GENAI_AVAILABLE,
        "models": {"openai": _openai.model, "gemini": _gemini.model}
    }

@app.post("/api/chat")
async def api_chat(payload: Dict[str, Any]):
    prompt = payload.get("prompt")
    if not prompt or not isinstance(prompt, str):
        raise HTTPException(status_code=400, detail="Missing 'prompt' string in request body")
    # Optional explicit provider override from frontend
    provider = payload.get("provider")
    o = payload.get("model_overrides", {}) or {}
    if "openai_model" in o: _openai.model = o.get("openai_model")
    if "vertex_model" in o: _gemini.model = o.get("vertex_model")
    try:
        return JSONResponse(_router.route(prompt, provider=provider))
    except Exception as e:
        logger.exception("Routing failed"); raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"name":"OMNI Hybrid AI","endpoints":["GET /health","GET /health/providers","POST /api/chat"],"openai_model":_openai.model,"vertex_model":_gemini.model}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT","8080")))