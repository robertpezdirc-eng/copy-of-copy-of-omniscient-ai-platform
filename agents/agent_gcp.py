from typing import List, Dict, Any
from fastapi import Body
from pydantic import BaseModel, Field

from .common import build_app


app = build_app("omni-gcp")


class CompareRequest(BaseModel):
    focus: List[str] = Field(default_factory=lambda: ["compute", "storage", "network", "ml"])


@app.post("/compare")
async def compare(req: CompareRequest = Body(...)):
    matrix = {
        "compute": {
            "gcp": ["GKE Autopilot", "Cloud Run", "GCE", "Batch"],
            "aws": ["EKS Fargate", "Lambda", "EC2", "Batch"],
            "azure": ["AKS", "Functions", "VM Scale Sets"],
            "notes": "Serverless containers (Cloud Run) vs Lambda/Azure Functions; pricing granularity differs.",
        },
        "storage": {
            "gcp": ["GCS", "Filestore", "Spanner", "Bigtable"],
            "aws": ["S3", "EFS", "DynamoDB", "Aurora"],
            "azure": ["Blob", "Files", "Cosmos DB"],
            "notes": "GCS strong consistency; Spanner global consistency trade-offs vs Aurora/Cosmos.",
        },
        "network": {
            "gcp": ["Global VPC", "Cloud CDN", "Cloud Armor"],
            "aws": ["VPC", "CloudFront", "Shield"],
            "azure": ["VNet", "Front Door", "WAF"],
            "notes": "GCP global load balancing; AWS has regional ALB/NLB; Azure Front Door global edge.",
        },
        "ml": {
            "gcp": ["Vertex AI", "TPUs"],
            "aws": ["SageMaker", "Inferentia/Trainium"],
            "azure": ["Azure ML", "NDv5 GPUs"],
            "notes": "Managed MLOps maturity differs; accelerator pricing varies.",
        },
    }
    res = {k: v for k, v in matrix.items() if k in set(req.focus)}
    return {"comparison": res}


class DeployPlanRequest(BaseModel):
    app_name: str
    region: str = "us-central1"
    components: List[str] = Field(default_factory=lambda: ["api", "worker", "db", "storage"])


@app.post("/deploy/plan")
async def deploy_plan(req: DeployPlanRequest = Body(...)):
    mapping = {
        "api": ["Cloud Run", "Cloud Endpoints", "Cloud Logging"],
        "worker": ["Cloud Run Jobs", "Pub/Sub", "Cloud Scheduler"],
        "db": ["Cloud SQL (Postgres)", "MemoryStore (Redis)"],
        "storage": ["GCS Standard", "Cloud CDN"],
    }
    plan = []
    for c in req.components:
        plan.append({"component": c, "services": mapping.get(c, ["Cloud Run"])})
    steps = [
        "Create project and enable required APIs",
        "Provision infra with Terraform (service accounts, networks, SQL, GCS)",
        "Build and push container images to Artifact Registry",
        "Deploy Cloud Run and configure traffic + min instances",
        "Set up monitoring dashboards and alerting",
    ]
    return {"app": req.app_name, "region": req.region, "plan": plan, "steps": steps}


class CostEstimateRequest(BaseModel):
    monthly_requests: int = 5_000_000
    avg_cpu_seconds: float = 0.2
    avg_memory_gb_seconds: float = 0.1


@app.post("/cost/estimate")
async def cost_estimate(req: CostEstimateRequest = Body(...)):
    # Rough illustrative estimate for Cloud Run-like pricing (not official)
    cpu_rate = 0.000024  # per vCPU-second
    mem_rate = 0.0000025  # per GB-second
    request_rate = 0.000002  # per request beyond free tier

    cpu_cost = req.monthly_requests * req.avg_cpu_seconds * cpu_rate
    mem_cost = req.monthly_requests * req.avg_memory_gb_seconds * mem_rate
    req_cost = max(0, req.monthly_requests - 2_000_000) * request_rate
    total = round(cpu_cost + mem_cost + req_cost, 2)
    return {"cpu_cost": round(cpu_cost, 2), "mem_cost": round(mem_cost, 2), "request_cost": round(req_cost, 2), "total": total}