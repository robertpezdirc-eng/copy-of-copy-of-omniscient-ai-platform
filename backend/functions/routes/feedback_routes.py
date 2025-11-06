"""
Feedback & User Feedback Routes
Provides endpoints for collecting user feedback, bug reports, and feature requests
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

router = APIRouter()


class FeedbackType(str, Enum):
    """Types of feedback"""
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    IMPROVEMENT = "improvement"
    GENERAL = "general"


class FeedbackStatus(str, Enum):
    """Feedback status"""
    NEW = "new"
    REVIEWING = "reviewing"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class FeedbackSubmission(BaseModel):
    """Feedback submission model"""
    type: FeedbackType
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    category: Optional[str] = None
    priority: Optional[str] = Field(default="medium", pattern="^(low|medium|high|critical)$")
    user_email: Optional[str] = None
    metadata: Optional[dict] = Field(default_factory=dict)


class Feedback(BaseModel):
    """Feedback response model"""
    id: str
    type: FeedbackType
    title: str
    description: str
    status: FeedbackStatus
    category: Optional[str] = None
    priority: str
    user_email: Optional[str] = None
    created_at: str
    updated_at: str
    votes: int = 0
    metadata: dict = Field(default_factory=dict)


@router.post("/submit", response_model=Feedback, tags=["Feedback"])
async def submit_feedback(submission: FeedbackSubmission):
    """
    Submit new feedback, bug report, or feature request
    
    - **type**: Type of feedback (bug, feature_request, improvement, general)
    - **title**: Brief title describing the feedback
    - **description**: Detailed description
    - **priority**: Priority level (low, medium, high, critical)
    """
    # In production, this would save to database
    feedback_id = f"fb_{int(datetime.utcnow().timestamp())}"
    
    feedback = Feedback(
        id=feedback_id,
        type=submission.type,
        title=submission.title,
        description=submission.description,
        status=FeedbackStatus.NEW,
        category=submission.category,
        priority=submission.priority or "medium",
        user_email=submission.user_email,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
        votes=0,
        metadata=submission.metadata or {}
    )
    
    return feedback


@router.get("/list", response_model=List[Feedback], tags=["Feedback"])
async def list_feedback(
    type: Optional[FeedbackType] = Query(default=None, description="Filter by feedback type"),
    status: Optional[FeedbackStatus] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=200, description="Number of items to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination")
):
    """
    List feedback submissions with optional filters
    
    - **type**: Filter by feedback type
    - **status**: Filter by status
    - **limit**: Number of items per page
    - **offset**: Pagination offset
    """
    # Mock data - would query database in production
    mock_feedback = [
        Feedback(
            id="fb_001",
            type=FeedbackType.BUG,
            title="API response timeout on large datasets",
            description="When requesting analytics for more than 1000 records, the API times out after 30 seconds.",
            status=FeedbackStatus.IN_PROGRESS,
            category="api",
            priority="high",
            user_email="user@example.com",
            created_at="2024-10-20T10:30:00Z",
            updated_at="2024-10-22T14:15:00Z",
            votes=15
        ),
        Feedback(
            id="fb_002",
            type=FeedbackType.FEATURE_REQUEST,
            title="Add support for GraphQL API",
            description="It would be great to have a GraphQL endpoint alongside the REST API for more flexible queries.",
            status=FeedbackStatus.REVIEWING,
            category="api",
            priority="medium",
            user_email="developer@company.com",
            created_at="2024-10-21T09:00:00Z",
            updated_at="2024-10-21T09:00:00Z",
            votes=42
        ),
        Feedback(
            id="fb_003",
            type=FeedbackType.IMPROVEMENT,
            title="Improve documentation for RAG endpoints",
            description="The RAG API documentation could benefit from more examples and use cases.",
            status=FeedbackStatus.NEW,
            category="documentation",
            priority="low",
            created_at="2024-10-22T15:30:00Z",
            updated_at="2024-10-22T15:30:00Z",
            votes=8
        )
    ]
    
    # Apply filters
    if type:
        mock_feedback = [fb for fb in mock_feedback if fb.type == type]
    if status:
        mock_feedback = [fb for fb in mock_feedback if fb.status == status]
    
    return mock_feedback[offset:offset + limit]


@router.get("/{feedback_id}", response_model=Feedback, tags=["Feedback"])
async def get_feedback(feedback_id: str):
    """Get detailed feedback information by ID"""
    # Mock data - would query database in production
    if feedback_id not in ["fb_001", "fb_002", "fb_003"]:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return Feedback(
        id=feedback_id,
        type=FeedbackType.BUG,
        title="API response timeout on large datasets",
        description="When requesting analytics for more than 1000 records, the API times out after 30 seconds.",
        status=FeedbackStatus.IN_PROGRESS,
        category="api",
        priority="high",
        user_email="user@example.com",
        created_at="2024-10-20T10:30:00Z",
        updated_at="2024-10-22T14:15:00Z",
        votes=15,
        metadata={"browser": "Chrome", "version": "118.0"}
    )


@router.post("/{feedback_id}/vote", tags=["Feedback"])
async def vote_feedback(feedback_id: str):
    """Upvote a feedback item to show support"""
    # In production, would update database and prevent duplicate votes
    return {
        "feedback_id": feedback_id,
        "votes": 16,
        "message": "Vote recorded successfully"
    }


@router.get("/stats/summary", tags=["Feedback"])
async def get_feedback_stats():
    """Get feedback statistics and summary"""
    return {
        "total_feedback": 247,
        "by_type": {
            "bug": 89,
            "feature_request": 112,
            "improvement": 38,
            "general": 8
        },
        "by_status": {
            "new": 45,
            "reviewing": 78,
            "in_progress": 56,
            "resolved": 62,
            "rejected": 6
        },
        "by_priority": {
            "critical": 12,
            "high": 34,
            "medium": 145,
            "low": 56
        },
        "trending": [
            {"id": "fb_002", "title": "Add support for GraphQL API", "votes": 42},
            {"id": "fb_015", "title": "Real-time notifications", "votes": 38},
            {"id": "fb_001", "title": "API response timeout on large datasets", "votes": 15}
        ]
    }
