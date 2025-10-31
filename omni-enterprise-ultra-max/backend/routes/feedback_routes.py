""""""

Continuous Feedback & Improvement RoutesOMNI Platform - Continuous Feedback & Improvement System

"""In-app feedback, NPS surveys, and feature prioritization

"""

from fastapi import APIRouter

from pydantic import BaseModelfrom fastapi import APIRouter, Body

from datetime import datetime, timezonefrom typing import List, Optional, Dict, Any

import uuidfrom datetime import datetime, timedelta

import random

router = APIRouter()

router = APIRouter()



class FeedbackSubmission(BaseModel):# ============================================================================

    category: str# FEEDBACK & SURVEYS

    rating: int# ============================================================================

    comment: str

    user_email: str@router.post("/feedback/submit")

async def submit_feedback(

    user_id: str = Body(...),

@router.post("/feedback/submit")    category: str = Body(...),

async def submit_feedback(feedback: FeedbackSubmission):    message: str = Body(...),

    """Submit user feedback"""    rating: Optional[int] = Body(None),

        screenshot: Optional[str] = Body(None)

    feedback_id = f"FB-{uuid.uuid4().hex[:10].upper()}"):

        """Submit user feedback"""

    return {    

        "feedback_id": feedback_id,    return {

        "status": "received",        "feedback_id": f"fb_{random.randint(10000, 99999)}",

        "message": "Thank you for your feedback!",        "status": "received",

        "submitted_at": datetime.now(timezone.utc).isoformat()        "message": "Thank you for your feedback!",

    }        "estimated_review_time": "2-3 business days",

        "submitted_at": datetime.now().isoformat()

    }

@router.get("/feedback/stats")

async def get_feedback_stats():@router.post("/surveys/nps/submit")

    """Get feedback statistics"""async def submit_nps_survey(

        user_id: str = Body(...),

    return {    score: int = Body(..., ge=0, le=10),

        "total_feedback": 1247,    comment: Optional[str] = Body(None)

        "average_rating": 4.6,):

        "sentiment": "positive",    """Submit NPS survey response"""

        "categories": {    

            "feature_request": 345,    category = "promoter" if score >= 9 else ("passive" if score >= 7 else "detractor")

            "bug_report": 123,    

            "general": 779    return {

        }        "survey_id": f"nps_{random.randint(10000, 99999)}",

    }        "score": score,

        "category": category,

        "message": "Thank you for your feedback!",

@router.get("/nps/score")        "submitted_at": datetime.now().isoformat()

async def get_nps_score():    }

    """Get Net Promoter Score"""

    @router.get("/surveys/nps/results")

    return {async def get_nps_results(timeframe: str = "30d"):

        "nps_score": 72,    """Get NPS survey results"""

        "promoters": 65,    

        "passives": 25,    promoters = random.randint(60, 75)

        "detractors": 10,    passives = random.randint(15, 25)

        "trend": "improving"    detractors = 100 - promoters - passives

    }    nps_score = promoters - detractors

    
    return {
        "timeframe": timeframe,
        "nps_score": nps_score,
        "promoters_percentage": promoters,
        "passives_percentage": passives,
        "detractors_percentage": detractors,
        "total_responses": random.randint(500, 2000),
        "trend": "increasing" if nps_score > 50 else "stable"
    }

@router.get("/features/requests")
async def list_feature_requests(sort_by: str = "votes"):
    """List feature requests sorted by votes"""
    
    requests = []
    for i in range(10):
        requests.append({
            "request_id": f"feat_{random.randint(1000, 9999)}",
            "title": f"Feature Request {i+1}",
            "description": "Sample feature description",
            "votes": random.randint(10, 500),
            "status": random.choice(["reviewing", "planned", "in_progress", "completed"]),
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
        })
    
    requests.sort(key=lambda x: x["votes"], reverse=True)
    return {"requests": requests, "total": len(requests)}

@router.post("/features/vote")
async def vote_feature_request(
    request_id: str = Body(...),
    user_id: str = Body(...)
):
    """Vote for a feature request"""
    
    return {
        "success": True,
        "request_id": request_id,
        "votes": random.randint(50, 500),
        "message": "Vote recorded successfully"
    }
