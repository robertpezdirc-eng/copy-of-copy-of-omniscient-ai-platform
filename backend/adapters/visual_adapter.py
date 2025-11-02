import os
import base64
from fastapi import UploadFile
from typing import Dict, Any

try:
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None

try:
    import google.generativeai as genai  # type: ignore
except Exception:
    genai = None

class VisualAdapter:
    def __init__(self) -> None:
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.openai = OpenAI(api_key=self.openai_key) if (OpenAI and self.openai_key) else None
        if genai and self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.gemini_model_default = "gemini-1.5-flash"
        else:
            self.gemini_model_default = None

    async def analyze(self, file: UploadFile, prompt: str = "Describe this image") -> Dict[str, Any]:
        data = await file.read()
        if not data:
            return {"error": "empty file"}
        b64 = base64.b64encode(data).decode("ascii")

        # Prefer OpenAI if configured; else Gemini
        if self.openai:
            # Use gpt-4o-mini vision with data URL
            content = [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": f"data:image/png;base64,{b64}"},
            ]
            resp = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": content}],
            )
            text = resp.choices[0].message.content
            return {"summary": text, "provider": "openai"}

        if genai and self.gemini_key:
            gm = self.gemini_model_default or "gemini-1.5-flash"
            m = genai.GenerativeModel(gm)
            # Gemini supports inline bytes via blob
            # For simplicity we pass base64 via prompt
            resp = m.generate_content([prompt, f"data:image/png;base64,{b64}"])
            text = getattr(resp, "text", "")
            return {"summary": text, "provider": "gemini"}

        return {"error": "No provider configured", "provider": None}