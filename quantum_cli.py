#!/usr/bin/env python3
"""
Unified Quantum CLI Orchestrator

Use as a single command-line to route requests to available agents:
- Text -> OmniBrainAdapter (OpenAI/Gemini based on config)
- audio:<path> -> AudioAdapter (transcribe)
- image:<path> -> VisualAdapter (analyze)
- url:<http(s)://...> -> NetAgentAdapter (fetch)

Interactive mode:
  python quantum_cli.py

One-shot mode (runs once and exits):
  python quantum_cli.py "url:https://example.com"
  python quantum_cli.py "Hello world"
  python quantum_cli.py "image:C:/path/to/photo.jpg"
  python quantum_cli.py "audio:C:/path/to/audio.wav"

Notes:
- Adapters are loaded from omni-platform/backend/adapters
- Requires dependencies used by backend (fastapi/starlette/httpx/openai/gemini where applicable)
"""

import os
import sys
import io
import json
import asyncio
from typing import Any, Dict, Optional
import subprocess
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

# Optional Vertex tool import
try:
    from orchestration.vertex_tools import generate_text as vertex_generate_text
except Exception:
    vertex_generate_text = None

# Ensure we can import adapters from backend
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(REPO_ROOT, "omni-platform", "backend")
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

# Import adapters
try:
    from adapters.omni_brain_adapter import OmniBrainAdapter
except Exception as e:
    OmniBrainAdapter = None
    print(f"[WARN] OmniBrainAdapter ni na voljo: {e}")

try:
    from adapters.audio_adapter import AudioAdapter
except Exception as e:
    AudioAdapter = None
    print(f"[WARN] AudioAdapter ni na voljo: {e}")

try:
    from adapters.visual_adapter import VisualAdapter
except Exception as e:
    VisualAdapter = None
    print(f"[WARN] VisualAdapter ni na voljo: {e}")

try:
    from adapters.net_agent_adapter import NetAgentAdapter
except Exception as e:
    NetAgentAdapter = None
    print(f"[WARN] NetAgentAdapter ni na voljo: {e}")

try:
    from adapters.meta_adapter import MetaAdapter
except Exception as e:
    MetaAdapter = None
    print(f"[WARN] MetaAdapter ni na voljo: {e}")

# Starlette UploadFile for simulating FastAPI uploads in CLI
try:
    from starlette.datastructures import UploadFile
except Exception:
    UploadFile = None

# -------- Defaults & helpers ---------

def _default_model_for(provider: Optional[str]) -> Optional[str]:
    p = (provider or "").lower()
    if p in ("openai", "oai"):
        return os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    if p in ("gemini", "vertex"):
        return os.getenv("GEMINI_MODEL") or os.getenv("VERTEX_MODEL") or "gemini-1.5-flash"
    if p in ("ollama", "meta"):
        return os.getenv("OLLAMA_MODEL") or os.getenv("META_MODEL") or "llama3"
    return None


def _run_ps1(action: str, args: Optional[list] = None) -> Dict[str, Any]:
    script_path = os.path.join(REPO_ROOT, "quantum-package", "run_quantum.ps1")
    if not os.path.isfile(script_path):
        return {"error": "run_quantum.ps1 ni najden", "action": action}
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path, action]
    if args:
        cmd.extend([str(a) for a in args])
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "action": action,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except Exception as e:
        return {"error": str(e), "action": action}


# -------- Agent wrappers (async) ---------
async def omni_brain_agent(prompt: str, provider: str = None, model: str = None) -> Dict[str, Any]:
    if OmniBrainAdapter is None:
        return {"error": "OmniBrainAdapter ni na voljo"}
    adapter = OmniBrainAdapter()
    payload = {"prompt": prompt}
    if provider:
        payload["provider"] = provider
    if model:
        payload["model"] = model
    try:
        result = await adapter.invoke(payload)
        return result if isinstance(result, dict) else {"result": result}
    except Exception as e:
        return {"error": f"OmniBrain napaka: {e}"}


async def audio_agent(path: str) -> Dict[str, Any]:
    if AudioAdapter is None:
        return {"error": "AudioAdapter ni na voljo"}
    if UploadFile is None:
        return {"error": "Starlette UploadFile ni na voljo"}
    if not os.path.isfile(path):
        return {"error": f"Audio datoteka ne obstaja: {path}"}
    with open(path, "rb") as f:
        data = f.read()
    up = UploadFile(filename=os.path.basename(path), file=io.BytesIO(data))
    adapter = AudioAdapter()
    try:
        text = await adapter.transcribe(up)
        return {"transcript": text}
    except Exception as e:
        return {"error": f"Audio transcribe napaka: {e}"}


async def visual_agent(path: str) -> Dict[str, Any]:
    if VisualAdapter is None:
        return {"error": "VisualAdapter ni na voljo"}
    if UploadFile is None:
        return {"error": "Starlette UploadFile ni na voljo"}
    if not os.path.isfile(path):
        return {"error": f"Image datoteka ne obstaja: {path}"}
    with open(path, "rb") as f:
        data = f.read()
    up = UploadFile(filename=os.path.basename(path), file=io.BytesIO(data))
    adapter = VisualAdapter()
    try:
        # Basic prompt; adapter may ignore or use defaults
        result = await adapter.analyze(up, prompt="Analyze image and summarize key details")
        return result if isinstance(result, dict) else {"result": result}
    except Exception as e:
        return {"error": f"Image analyze napaka: {e}"}


async def net_agent(url: str) -> Dict[str, Any]:
    if NetAgentAdapter is None:
        return {"error": "NetAgentAdapter ni na voljo"}
    adapter = NetAgentAdapter()
    try:
        result = await adapter.fetch(url)
        # Ensure result is JSON-serializable
        if isinstance(result, (str, bytes)):
            return {"result": result.decode("utf-8") if isinstance(result, bytes) else result}
        return result
    except Exception as e:
        return {"error": f"Net-agent napaka: {e}"}


# Optional Meta/Ollama stub
async def meta_agent(user_input: str, provider: str = "ollama", model: str = None) -> Dict[str, Any]:
    if MetaAdapter is None:
        return {"error": "MetaAdapter ni na voljo"}
    adapter = MetaAdapter()
    try:
        result = await adapter.generate(prompt=user_input, model=model, provider=provider)
        return result if isinstance(result, dict) else {"result": result}
    except Exception as e:
        return {"error": f"Meta/Ollama napaka: {e}"}


def vertex_agent(prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
    if vertex_generate_text is None:
        return {"error": "Vertex AI tools unavailable"}
    try:
        res = vertex_generate_text(prompt=prompt, model=model)
        return res if isinstance(res, dict) else {"result": res}
    except Exception as e:
        return {"error": f"Vertex napaka: {e}"}


# ---------- Orchestrator ----------
def run_command(user_input: str, provider: str = None, model: str = None) -> Dict[str, Any]:
    u = user_input.strip()
    # Lifecycle commands via PowerShell script
    if u.lower() == "start":
        return _run_ps1("start")
    if u.lower() == "stop":
        return _run_ps1("stop")
    if u.lower().startswith("scale"):
        parts = u.split()
        n = None
        for p in parts[1:]:
            if p.isdigit():
                n = int(p)
                break
            if "=" in p:
                try:
                    n = int(p.split("=", 1)[1])
                    break
                except Exception:
                    pass
        if n is None:
            return {"error": "Uporaba: scale <število>"}
        return _run_ps1("scale", [n])
    if u.lower() == "health":
        return run_health_report()
    try:
        # Explicit provider routing if specified
        if provider in ("ollama", "meta"):
            m = model or _default_model_for(provider)
            return asyncio.run(meta_agent(u, provider=provider, model=m))
        if provider in ("openai", "gemini"):
            m = model or _default_model_for(provider)
            return asyncio.run(omni_brain_agent(u, provider=provider, model=m))
        if provider in ("vertex",):
            m = model or _default_model_for("vertex")
            return vertex_agent(u, model=m)
        # Prefix-based routing fallback
        if u.lower().startswith("audio:"):
            path = u[6:].strip()
            return asyncio.run(audio_agent(path))
        elif u.lower().startswith("image:"):
            path = u[6:].strip()
            return asyncio.run(visual_agent(path))
        elif u.lower().startswith("url:"):
            url = u[4:].strip()
            return asyncio.run(net_agent(url))
        elif "meta" in u.lower():
            m = _default_model_for("ollama")
            return asyncio.run(meta_agent(u, provider="ollama", model=m))
        else:
            # Default to OmniBrain; choose provider by env DEFAULT_PROVIDER
            default_provider = (os.getenv("DEFAULT_PROVIDER") or "").lower() or None
            m = _default_model_for(default_provider or "openai")
            return asyncio.run(omni_brain_agent(u, provider=default_provider, model=m))
    except KeyboardInterrupt:
        return {"error": "Prekinjeno"}


def _print_json(result: Dict[str, Any]) -> None:
    try:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception:
        print(result)


def _print_help() -> None:
    print(
        """
Uporaba:
  Interaktivno: python quantum_cli.py
  Enkratni ukaz: python quantum_cli.py "<ukaz>"

Primeri:
  python quantum_cli.py "Hello world"
  python quantum_cli.py "url:https://example.com"
  python quantum_cli.py "image:C:/slika.jpg"
  python quantum_cli.py "audio:C:/zvok.wav"
        """.strip()
    )
def _print_help() -> None:
    print(
        """
Uporaba:
  Interaktivno: python quantum_cli.py
  Enkratni ukaz: python quantum_cli.py "<ukaz>" [--provider <openai|gemini|ollama|meta>] [--model <ime_modela>]

Primeri:
  python quantum_cli.py "Hello world"
  python quantum_cli.py --provider openai --model gpt-4o-mini "Hello world"
  python quantum_cli.py --provider ollama --model llama3 "Pozdravljen orkestrator!"
  python quantum_cli.py "url:https://example.com"
  python quantum_cli.py "image:C:/slika.jpg"
  python quantum_cli.py "audio:C:/zvok.wav"
  python quantum_cli.py health
        """.strip()
    )


def run_health_report() -> Dict[str, Any]:
    script_path = os.path.join(REPO_ROOT, "quantum-package", "run_quantum.ps1")
    report: Dict[str, Any] = {"script_used": False, "results": {}}
    if os.path.isfile(script_path):
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path, "test"],
                capture_output=True,
                text=True,
            )
            report["script_used"] = True
            report["exit_code"] = proc.returncode
            report["stdout"] = proc.stdout
            report["stderr"] = proc.stderr
            return report
        except Exception as e:
            report["script_error"] = str(e)
    # Fallback: hit known endpoints
    endpoints = {
        "platform": "http://localhost:8080/health",
        "gateway": "http://localhost:8082/api/v1/health",
        "worker": "http://localhost:8084/worker/health",
    }
    timeout = float(os.getenv("HEALTH_TIMEOUT", "3"))
    retries = int(os.getenv("HEALTH_RETRIES", "3"))
    report["results"] = _http_health_endpoints(endpoints, timeout=timeout, retries=retries)
    return report


def _http_health_endpoints(endpoints: Dict[str, str], timeout: float = 3.0, retries: int = 3) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    for name, url in endpoints.items():
        last_error = None
        for attempt in range(1, retries + 1):
            try:
                with urlopen(url, timeout=timeout) as resp:
                    code = resp.getcode()
                    body = resp.read(256).decode("utf-8", errors="ignore")
                    results[name] = {"status_code": code, "body": body, "attempt": attempt}
                    break
            except HTTPError as he:
                last_error = {"error": f"HTTPError {he.code}", "url": url, "attempt": attempt}
            except URLError as ue:
                last_error = {"error": str(ue.reason), "url": url, "attempt": attempt}
            except Exception as e:
                last_error = {"error": str(e), "url": url, "attempt": attempt}
        if name not in results:
            results[name] = last_error or {"error": "Unknown", "url": url}
    return results


def _print_help() -> None:
    print(
        """
Uporaba:
  Interaktivno: python quantum_cli.py
  Enkratni ukaz: python quantum_cli.py "<ukaz>"

Primeri:
  python quantum_cli.py "Hello world"
  python quantum_cli.py "url:https://example.com"
  python quantum_cli.py "image:C:/slika.jpg"
  python quantum_cli.py "audio:C:/zvok.wav"
        """.strip()
    )


def _print_help() -> None:
    print(
        """
Uporaba:
  Interaktivno: python quantum_cli.py
  Enkratni ukaz: python quantum_cli.py "<ukaz>" [--provider <openai|gemini|vertex|ollama|meta>] [--model <ime_modela>]

Primeri:
  python quantum_cli.py "Hello world"
  python quantum_cli.py --provider openai --model gpt-4o-mini "Pozdravljen orkestrator!"
  python quantum_cli.py --provider gemini --model gemini-1.5-flash "Pozdravljen orkestrator!"
  python quantum_cli.py --provider vertex --model gemini-1.5-flash "Pozdravljen orkestrator!"
  python quantum_cli.py --provider ollama --model llama3 "Pozdravljen orkestrator!"
  python quantum_cli.py "url:https://example.com"
  python quantum_cli.py "image:C:/slika.jpg"
  python quantum_cli.py "audio:C:/zvok.wav"
  python quantum_cli.py health
  python quantum_cli.py start
  python quantum_cli.py stop
  python quantum_cli.py "scale 4"
        """.strip()
    )


if __name__ == "__main__":
    # One-shot mode with optional provider/model flags
    if len(sys.argv) > 1:
        provider = None
        model = None
        parts = []
        i = 1
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg.startswith("--provider="):
                provider = arg.split("=", 1)[1].strip().lower()
            elif arg == "--provider" and i + 1 < len(sys.argv):
                provider = sys.argv[i + 1].strip().lower()
                i += 1
            elif arg.startswith("--model="):
                model = arg.split("=", 1)[1].strip()
            elif arg == "--model" and i + 1 < len(sys.argv):
                model = sys.argv[i + 1].strip()
                i += 1
            else:
                parts.append(arg)
            i += 1
        cmd = " ".join(parts).strip()
        if cmd in ("-h", "--help", "help") or not cmd:
            _print_help()
            sys.exit(0)
        result = run_command(cmd, provider=provider, model=model)
        _print_json(result)
        sys.exit(0)

    # Interactive mode
    print("Quantum CLI orchestrator (exit/quit za izhod). Vnesi ukaz:")
    while True:
        try:
            cmd = input("> ").strip()
        except EOFError:
            break
        if cmd.lower() in ("exit", "quit"):
            break
        if cmd.lower() in ("help", "-h", "--help"):
            _print_help()
            continue
        if not cmd:
            continue
        result = run_command(cmd)
        _print_json(result)