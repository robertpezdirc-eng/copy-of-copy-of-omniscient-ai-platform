import os
from typing import Any, Dict

# OpenAI
try:
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None  # runtime fallback

# Google Gemini
try:
    import google.generativeai as genai  # type: ignore
except Exception:
    genai = None  # runtime fallback

class OmniBrainAdapter:
    def __init__(self) -> None:
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.openai = OpenAI(api_key=self.openai_key) if (OpenAI and self.openai_key) else None
        if genai and self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.gemini_model_default = "gemini-1.5-flash"
        else:
            self.gemini_model_default = None

    async def invoke(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = payload.get("prompt", "")
        model = payload.get("model")
        temperature = float(payload.get("temperature") or 0.7)
        provider = (payload.get("provider") or "auto").lower()

        # Choose provider: explicit provider > model hint > default
        use_openai = False
        use_gemini = False
        if provider == "openai":
            use_openai = True
        elif provider == "gemini":
            use_gemini = True
        elif model and model.lower().startswith("gpt"):
            use_openai = True
        else:
            use_gemini = True if self.gemini_model_default else True if self.openai else False

        try:
            if use_openai and self.openai:
                resp = self.openai.chat.completions.create(
                    model=model or "gpt-4o-mini",
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = resp.choices[0].message.content
                return {"reply": text, "provider": "openai", "model": model or "gpt-4o-mini"}

            if use_gemini and genai and self.gemini_key:
                gm = model or self.gemini_model_default or "gemini-1.5-flash"
                m = genai.GenerativeModel(gm)
                resp = m.generate_content(prompt)
                text = getattr(resp, "text", None) or (resp.candidates[0].content.parts[0].text if getattr(resp, "candidates", None) else "")
                return {"reply": text, "provider": "gemini", "model": gm}
        except Exception as e:
            return {"error": str(e), "provider": "openai" if use_openai else "gemini", "model": model}

        return {
            "error": "No provider configured. Set OPENAI_API_KEY or GEMINI_API_KEY/GOOGLE_API_KEY.",
            "reply": "",
            "provider": provider,
            "model": model,
        }

    async def stream(self, payload: Dict[str, Any]):
        prompt = payload.get("prompt", "")
        model = payload.get("model")
        temperature = float(payload.get("temperature") or 0.7)
        provider = (payload.get("provider") or "auto").lower()

        use_openai = False
        use_gemini = False
        if provider == "openai":
            use_openai = True
        elif provider == "gemini":
            use_gemini = True
        elif model and model.lower().startswith("gpt"):
            use_openai = True
        else:
            use_openai = bool(self.openai)
            use_gemini = not use_openai and bool(self.gemini_key)

        try:
            if use_openai and self.openai:
                stream = self.openai.chat.completions.create(
                    model=model or "gpt-4o-mini",
                    temperature=temperature,
                    stream=True,
                    messages=[{"role": "user", "content": prompt}],
                )
                for chunk in stream:
                    delta = None
                    try:
                        delta = chunk.choices[0].delta.content
                    except Exception:
                        delta = None
                    if delta:
                        yield delta
                return

            if use_gemini and genai and self.gemini_key:
                gm = model or self.gemini_model_default or "gemini-1.5-flash"
                m = genai.GenerativeModel(gm)
                stream = m.generate_content(prompt, stream=True)
                for chunk in stream:
                    text = getattr(chunk, "text", None)
                    if text:
                        yield text
                return
        except Exception as e:
            yield f"[error] {e}"
            return

        # Fallback: non-streaming chunking of full response
        full = await self.invoke(payload)
        reply = full.get("reply") or full.get("error") or ""
        for i in range(0, len(reply), 64):
            yield reply[i:i+64]