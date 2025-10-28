from .common import build_app

app = build_app("rl_core")


@app.post("/train")
async def train(cfg: dict):
    # Stub training endpoint
    return {"status": "started", "config": cfg}