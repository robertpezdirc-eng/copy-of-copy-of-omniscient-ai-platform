from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from orchestration.agentic_orchestrator import router as orchestration_router

app = FastAPI(title="Orchestrator Test App")

# Enable CORS for local React dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount orchestration API router
app.include_router(orchestration_router)