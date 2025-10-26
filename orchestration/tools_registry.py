from typing import Dict, Any

# Minimal tool registry for MVP
# Expand later to wrap existing modules/services uniformly

# Optional Vertex tool import (safe fail if SDK missing)
try:
    from .vertex_tools import generate_text as _vertex_generate_text
except Exception:
    _vertex_generate_text = None


def available_tools() -> Dict[str, str]:
    return {
        "echo": "Echo back the provided text and context",
        "gemini_text": "Generate text via Vertex AI Gemini",
    }


def execute_tool(tool: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    if tool == "echo":
        return {"ok": True, "output": inputs.get("text"), "context": inputs.get("context")}
    if tool == "gemini_text":
        if not _vertex_generate_text:
            return {"ok": False, "error": "Vertex AI tools unavailable"}
        prompt = inputs.get("text") or inputs.get("prompt") or ""
        model = inputs.get("model")
        system_instruction = inputs.get("system") or inputs.get("system_instruction")
        cfg = inputs.get("config") or {}
        res = _vertex_generate_text(prompt=prompt, model=model, system_instruction=system_instruction, config=cfg)
        if res.get("ok"):
            return {"ok": True, "output": res.get("text"), "model": res.get("model")}
        return res
    return {"ok": False, "error": f"Unknown tool '{tool}'"}