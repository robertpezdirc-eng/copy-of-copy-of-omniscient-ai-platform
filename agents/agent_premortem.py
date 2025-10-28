from .common import build_app

app = build_app("premortem_tester")


@app.post("/plan")
async def plan(spec: dict):
    risks = [
        {"risk": "deployment_misconfig", "impact": "high"},
        {"risk": "scaling_limits", "impact": "medium"},
    ]
    return {"plan": {"tests": ["load", "chaos", "rollback"], "risks": risks}, "spec": spec}