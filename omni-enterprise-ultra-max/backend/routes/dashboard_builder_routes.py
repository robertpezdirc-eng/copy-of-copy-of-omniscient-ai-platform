"""
Dashboard Builder API Routes
Endpoints for building dashboards using Ollama
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from services.ai.dashboard_builder_service import get_dashboard_builder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dashboards", tags=["Dashboard Builder"])


class BuildRequest(BaseModel):
    """Request to build dashboards."""
    priority_filter: Optional[int] = Field(None, ge=1, le=3, description="Filter by priority: 1=high, 2=medium, 3=low")
    save_to_disk: bool = Field(True, description="Save generated dashboards to files")
    output_dir: str = Field("dashboards/generated", description="Output directory for generated dashboards")


class BuildResponse(BaseModel):
    """Response from dashboard build."""
    status: str
    message: str
    total_dashboards: int
    dashboards: List[dict]


@router.get("/types")
async def list_dashboard_types():
    """
    List all available dashboard types that can be built.
    
    Returns:
        List of dashboard types with descriptions and priorities
    """
    builder = get_dashboard_builder()
    return {
        "total": len(builder.dashboard_types),
        "dashboards": builder.dashboard_types
    }


@router.post("/build", response_model=BuildResponse)
async def build_dashboards(request: BuildRequest, background_tasks: BackgroundTasks):
    """
    Build dashboards using Ollama AI.
    
    This endpoint uses Ollama to generate React TypeScript dashboard components
    based on the platform's API endpoints and data structures.
    
    Args:
        request: Build configuration
        
    Returns:
        Generated dashboards with code
        
    Example:
        ```bash
        curl -X POST http://localhost:8080/api/v1/dashboards/build \\
          -H "Content-Type: application/json" \\
          -d '{"priority_filter": 1, "save_to_disk": true}'
        ```
    """
    try:
        builder = get_dashboard_builder()
        
        # Check if Ollama is enabled
        if not builder.ollama.enabled:
            logger.warning("Ollama not enabled, will use templates")
        
        # Build dashboards
        logger.info(f"Starting dashboard build (priority_filter={request.priority_filter})")
        dashboards = await builder.build_all_dashboards(priority_filter=request.priority_filter)
        
        # Save to disk if requested
        if request.save_to_disk:
            background_tasks.add_task(
                builder.save_dashboards,
                dashboards,
                request.output_dir
            )
        
        return BuildResponse(
            status="success",
            message=f"Successfully built {len(dashboards)} dashboards",
            total_dashboards=len(dashboards),
            dashboards=dashboards
        )
        
    except Exception as e:
        logger.error(f"Error building dashboards: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to build dashboards: {str(e)}")


@router.get("/build/status")
async def get_build_status():
    """
    Get the status of the dashboard builder.
    
    Returns:
        Builder configuration and Ollama status
    """
    builder = get_dashboard_builder()
    ollama_health = await builder.ollama.health_check()
    
    return {
        "ollama": ollama_health,
        "github_repo": builder.github_repo,
        "cloud_run_base": builder.cloud_run_base,
        "total_dashboard_types": len(builder.dashboard_types),
        "ready": ollama_health.get("status") == "healthy"
    }


@router.post("/build/{dashboard_name}")
async def build_single_dashboard(dashboard_name: str, background_tasks: BackgroundTasks):
    """
    Build a single dashboard by name.
    
    Args:
        dashboard_name: Name of the dashboard (e.g., "Revenue Analytics")
        
    Returns:
        Generated dashboard code
    """
    try:
        builder = get_dashboard_builder()
        
        # Find dashboard type
        dashboard_type = next(
            (d for d in builder.dashboard_types if d["name"].lower() == dashboard_name.lower()),
            None
        )
        
        if not dashboard_type:
            raise HTTPException(
                status_code=404,
                detail=f"Dashboard type '{dashboard_name}' not found. Use /types to list available types."
            )
        
        # Build dashboard
        dashboard = await builder.build_dashboard(dashboard_type)
        
        return {
            "status": "success",
            "dashboard": dashboard
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building dashboard {dashboard_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generated")
async def list_generated_dashboards(output_dir: str = "dashboards/generated"):
    """
    List all generated dashboard files.
    
    Args:
        output_dir: Directory where dashboards are saved
        
    Returns:
        List of generated dashboard files
    """
    import os
    import json
    
    manifest_path = os.path.join(output_dir, "manifest.json")
    
    if not os.path.exists(manifest_path):
        return {
            "status": "no_dashboards",
            "message": "No dashboards have been generated yet. Use /build to generate them."
        }
    
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        return {
            "status": "success",
            "manifest": manifest
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading manifest: {str(e)}")
