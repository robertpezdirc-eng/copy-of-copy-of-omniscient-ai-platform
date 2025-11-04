# Backend Development Best Practices & Standards

## Overview

This document establishes coding standards, best practices, and patterns for backend development in the Omni Enterprise Ultra Max platform.

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── main_minimal.py         # Minimal startup mode
├── database.py             # Database initialization
├── alembic/                # Database migrations
├── models/                 # SQLAlchemy/Pydantic models
├── routes/                 # API route handlers (44 files)
├── services/               # Business logic services
├── middleware/             # Request/response middleware
├── adapters/               # External service adapters
├── utils/                  # Utility functions
├── observability/          # Monitoring and logging
└── tests/                  # Test files
```

## Coding Standards

### 1. Import Organization

**Always use relative imports** for internal modules:

✅ **DO**:
```python
from services.ai.rag_service import RAGService
from models.user import User
from utils.logging_filters import PIIRedactionFilter
```

❌ **DON'T**:
```python
from backend.services.ai.rag_service import RAGService
from backend.models.user import User
```

### 2. Type Hints

**Always use type hints** for function parameters and return types:

✅ **DO**:
```python
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

async def get_user(user_id: str) -> Optional[User]:
    """Get user by ID."""
    return await db.users.find_one({"id": user_id})

def process_data(items: List[Dict[str, Any]]) -> Dict[str, int]:
    """Process data items and return statistics."""
    return {"count": len(items)}
```

❌ **DON'T**:
```python
async def get_user(user_id):
    return await db.users.find_one({"id": user_id})
```

### 3. Pydantic Models

**Use Pydantic for request/response validation:**

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    """User creation request."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., min_length=1, description="Full name")
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email address')
        return v.lower()

class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    full_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### 4. Route Structure

**Organize routes with clear patterns:**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from models.user import User
from services.user_service import UserService

# Create router with tags
router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"]
)

# Dependency injection
async def get_user_service() -> UserService:
    return UserService()

@router.get(
    "/",
    response_model=List[UserResponse],
    summary="List all users",
    description="Retrieve a paginated list of users"
)
async def list_users(
    page: int = 1,
    per_page: int = 20,
    service: UserService = Depends(get_user_service)
) -> List[UserResponse]:
    """List users with pagination."""
    try:
        users = await service.list_users(page=page, per_page=per_page)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID"
)
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Get a specific user by ID."""
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    return user

@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user"
)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Create a new user."""
    return await service.create(user_data)
```

### 5. Service Layer

**Implement business logic in service classes:**

```python
from typing import List, Optional
from models.user import User
from database import get_mongodb

class UserService:
    """User business logic service."""
    
    def __init__(self):
        self.db = get_mongodb()
        self.collection = self.db.users
    
    async def list_users(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[dict] = None
    ) -> List[User]:
        """List users with pagination."""
        skip = (page - 1) * per_page
        query = filters or {}
        
        cursor = self.collection.find(query).skip(skip).limit(per_page)
        users = await cursor.to_list(length=per_page)
        
        return [User(**user) for user in users]
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        user_doc = await self.collection.find_one({"id": user_id})
        return User(**user_doc) if user_doc else None
    
    async def create(self, user_data: UserCreate) -> User:
        """Create new user."""
        user = User(
            id=generate_uuid(),
            email=user_data.email,
            full_name=user_data.full_name,
            created_at=datetime.utcnow()
        )
        
        await self.collection.insert_one(user.dict())
        return user
    
    async def update(self, user_id: str, updates: dict) -> Optional[User]:
        """Update user."""
        result = await self.collection.update_one(
            {"id": user_id},
            {"$set": updates}
        )
        
        if result.modified_count == 0:
            return None
            
        return await self.get_by_id(user_id)
    
    async def delete(self, user_id: str) -> bool:
        """Delete user."""
        result = await self.collection.delete_one({"id": user_id})
        return result.deleted_count > 0
```

### 6. Error Handling

**Use consistent error handling patterns:**

```python
from fastapi import HTTPException, status
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ServiceError(Exception):
    """Base service error."""
    pass

class NotFoundError(ServiceError):
    """Resource not found."""
    pass

class ValidationError(ServiceError):
    """Validation failed."""
    pass

# In routes
@router.get("/{user_id}")
async def get_user(user_id: str):
    try:
        user = await user_service.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error getting user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

### 7. Async Operations

**Use async/await for I/O operations:**

✅ **DO**:
```python
async def fetch_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()

async def save_to_db(data: dict):
    await db.collection.insert_one(data)
```

❌ **DON'T** (blocking operations in async context):
```python
async def fetch_data():
    response = requests.get("https://api.example.com/data")  # Blocking!
    return response.json()
```

### 8. Database Operations

**Use proper database patterns:**

```python
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Database operations service."""
    
    def __init__(self, collection_name: str):
        self.collection = get_mongodb()[collection_name]
    
    async def find_one(
        self,
        query: dict,
        projection: Optional[dict] = None
    ) -> Optional[dict]:
        """Find single document."""
        try:
            return await self.collection.find_one(query, projection)
        except Exception as e:
            logger.error(f"Error finding document: {e}")
            raise
    
    async def find_many(
        self,
        query: dict,
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[dict]:
        """Find multiple documents."""
        cursor = self.collection.find(query)
        
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        
        return await cursor.to_list(length=limit)
    
    async def insert_one(self, document: dict) -> str:
        """Insert single document."""
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)
    
    async def update_one(
        self,
        query: dict,
        update: dict,
        upsert: bool = False
    ) -> int:
        """Update single document."""
        result = await self.collection.update_one(
            query,
            {"$set": update},
            upsert=upsert
        )
        return result.modified_count
    
    async def delete_one(self, query: dict) -> int:
        """Delete single document."""
        result = await self.collection.delete_one(query)
        return result.deleted_count
```

### 9. Authentication & Authorization

**Implement proper security:**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user = await user_service.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def require_role(required_role: str):
    """Dependency to require specific role."""
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    return role_checker

# Usage
@router.get("/admin/users")
async def list_users(user: User = Depends(require_role("admin"))):
    """Admin-only endpoint."""
    return await user_service.list_all()
```

### 10. Testing

**Write comprehensive tests:**

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_create_user():
    """Test user creation."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/users",
            json={
                "email": "test@example.com",
                "password": "Password123",
                "full_name": "Test User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data

@pytest.mark.asyncio
async def test_get_user_not_found():
    """Test getting non-existent user."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/users/nonexistent")
        assert response.status_code == 404
```

## Configuration Management

### Environment Variables

```python
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "Omni Enterprise Ultra Max"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Database
    MONGODB_URL: str
    POSTGRES_URL: str
    REDIS_URL: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # External Services
    OPENAI_API_KEY: Optional[str] = None
    STRIPE_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## Logging

### Standard Logging Pattern

```python
import logging
from utils.logging_filters import PIIRedactionFilter

# Configure logger
logger = logging.getLogger(__name__)
logger.addFilter(PIIRedactionFilter())

# Usage
logger.info(f"Processing request for user {user_id}")
logger.warning(f"Rate limit approaching for tenant {tenant_id}")
logger.error(f"Failed to process payment: {error}", exc_info=True)
```

## Performance Best Practices

### 1. Database Indexing

```python
# Create indexes for frequently queried fields
await collection.create_index("email", unique=True)
await collection.create_index([("tenant_id", 1), ("created_at", -1)])
```

### 2. Caching

```python
from functools import lru_cache
import redis

# In-memory caching
@lru_cache(maxsize=128)
def get_config(key: str) -> str:
    """Get configuration value (cached)."""
    return config[key]

# Redis caching
async def get_cached_user(user_id: str) -> Optional[User]:
    """Get user from cache or database."""
    cache_key = f"user:{user_id}"
    
    # Try cache first
    cached = await redis_client.get(cache_key)
    if cached:
        return User(**json.loads(cached))
    
    # Fetch from database
    user = await db.users.find_one({"id": user_id})
    if user:
        # Cache for 5 minutes
        await redis_client.setex(
            cache_key,
            300,
            json.dumps(user)
        )
    
    return User(**user) if user else None
```

### 3. Background Tasks

```python
from fastapi import BackgroundTasks

async def send_email(to: str, subject: str, body: str):
    """Send email (background task)."""
    # Email sending logic
    pass

@router.post("/users")
async def create_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks
):
    """Create user and send welcome email."""
    user = await user_service.create(user_data)
    
    # Send email in background
    background_tasks.add_task(
        send_email,
        to=user.email,
        subject="Welcome!",
        body="Welcome to our platform"
    )
    
    return user
```

## Security Best Practices

### 1. Input Validation

```python
from pydantic import BaseModel, validator, Field

class UserInput(BaseModel):
    email: str = Field(..., max_length=255)
    username: str = Field(..., min_length=3, max_length=30)
    
    @validator('email')
    def validate_email(cls, v):
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain alphanumeric characters, - and _')
        return v
```

### 2. SQL Injection Prevention

```python
# Use parameterized queries
from sqlalchemy import text

# ✅ DO
result = await db.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": user_email}
)

# ❌ DON'T
result = await db.execute(
    f"SELECT * FROM users WHERE email = '{user_email}'"  # Vulnerable!
)
```

### 3. Rate Limiting

```python
from fastapi import Request
from middleware.rate_limiter import RateLimiter

rate_limiter = RateLimiter(requests_per_minute=60)

@router.get("/data")
async def get_data(request: Request):
    """Rate-limited endpoint."""
    await rate_limiter.check_rate_limit(request.client.host)
    return {"data": "..."}
```

## Documentation

### 1. Docstrings

```python
def process_payment(
    amount: float,
    currency: str,
    payment_method: str
) -> PaymentResult:
    """
    Process a payment transaction.
    
    Args:
        amount: Payment amount in the specified currency
        currency: ISO 4217 currency code (e.g., 'USD', 'EUR')
        payment_method: Payment method ID
    
    Returns:
        PaymentResult: Result of the payment processing
    
    Raises:
        ValidationError: If amount is negative or currency is invalid
        PaymentError: If payment processing fails
    
    Example:
        >>> result = process_payment(99.99, 'USD', 'card_123')
        >>> print(result.status)
        'success'
    """
    pass
```

### 2. OpenAPI Documentation

```python
@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user account with email and password",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Invalid input"},
        409: {"description": "User already exists"},
    },
    tags=["users"]
)
async def create_user(user_data: UserCreate):
    """Create a new user account."""
    pass
```

## Deployment Modes

### 1. Standalone Mode

Default mode with all features enabled.

### 2. Internal Mode

Run as internal service behind gateway:

```python
RUN_AS_INTERNAL=1
```

### 3. Minimal Mode

Lightweight mode for Cloud Run:

```python
OMNI_MINIMAL=1
```

## Summary Checklist

✅ Use relative imports
✅ Add type hints everywhere
✅ Use Pydantic for validation
✅ Implement proper error handling
✅ Use async/await for I/O
✅ Add comprehensive logging
✅ Implement caching where appropriate
✅ Write tests for all endpoints
✅ Add proper documentation
✅ Use dependency injection
✅ Implement security best practices
✅ Follow consistent naming conventions
✅ Keep routes thin, logic in services
✅ Use background tasks for long operations
✅ Validate and sanitize all inputs

These standards ensure maintainable, secure, and performant backend code.
