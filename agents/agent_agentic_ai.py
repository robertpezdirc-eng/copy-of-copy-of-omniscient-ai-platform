from .common import build_app

app = build_app("agentic_ai")

# Example endpoint for orchestration
@app.post("/act")
async def act(payload: dict):
    return {"agent": "agentic_ai", "action": "received", "payload": payload}