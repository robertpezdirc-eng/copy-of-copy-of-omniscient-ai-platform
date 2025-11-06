"""
Database Configuration & Connection Management
Supports: PostgreSQL, MySQL, MongoDB, Redis, Firestore
"""

import os
from typing import Optional, Any, Callable, Type
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import json
from functools import wraps
import inspect

# Pydantic is a soft dependency, so we handle its absence gracefully.
_pydantic_installed = False
try:
    from pydantic import BaseModel
    _pydantic_installed = True
except ImportError:
    class BaseModel:  # type: ignore
        pass  # Dummy class if pydantic is not installed

# Make motor import optional and non-fatal
AsyncIOMotorClient = None
try:
    from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
except Exception as _mongo_import_err:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        f"MongoDB driver not available (motor import failed): {_mongo_import_err}. Mongo features disabled."
    )

import redis.asyncio as aioredis
from google.cloud import firestore
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# Database URLs from environment
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/omni")
MYSQL_URL = os.getenv("MYSQL_URL", "mysql://user:pass@localhost:3306/omni")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# PostgreSQL Engine with optimized pooling
postgres_engine = create_engine(
    POSTGRES_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=int(os.getenv("DB_POOL_SIZE", "20")),  # Increased default for Cloud Run
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "40")),  # More overflow capacity
    pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),  # Recycle connections hourly
    pool_timeout=30,  # Wait up to 30s for connection from pool
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    connect_args={
        "connect_timeout": 10,  # 10s connection timeout
        "options": "-c statement_timeout=30000"  # 30s query timeout
    }
)

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)

# MongoDB Client
mongodb_client: Optional["AsyncIOMotorClient"] = None
mongodb_db = None

# Redis Client
redis_client: Optional[aioredis.Redis] = None

# Firestore Client
firestore_client: Optional[firestore.Client] = None


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_mongodb():
    return mongodb_db


async def get_redis():
    return redis_client


def get_firestore():
    return firestore_client


async def init_databases():
    global mongodb_client, mongodb_db, redis_client, firestore_client
    logger.info("Initializing database connections...")

    # PostgreSQL
    try:
        try:
            from models import gdpr as _gdpr_models  # noqa: F401
            from models import tickets as _tickets_models # noqa: F401
        except Exception as _model_err:
            logger.warning(f"Model import warning (tables may be missing): {_model_err}")

        Base.metadata.create_all(bind=postgres_engine)
        logger.info("✅ PostgreSQL connected")
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")

    # MongoDB (optional)
    if AsyncIOMotorClient is None:
        logger.info("MongoDB driver not installed; skipping Mongo initialization")
    else:
        try:
            mongodb_client = AsyncIOMotorClient(MONGODB_URL)
            mongodb_db = mongodb_client[os.getenv("MONGODB_DB", "omni")]
            await mongodb_client.server_info()  # Test connection
            logger.info("✅ MongoDB connected")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")

    # Redis
    try:
        redis_client = await aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")

    # Firestore
    try:
        project_id = os.getenv("GCP_PROJECT_ID")
        if project_id:
            firestore_client = firestore.Client(project=project_id)
            logger.info("✅ Firestore connected")
        else:
            logger.warning("⚠️ GCP_PROJECT_ID not set, Firestore not initialized")
    except Exception as e:
        logger.error(f"❌ Firestore connection failed: {e}")

    logger.info("Database initialization complete")


async def close_databases():
    global mongodb_client, redis_client
    logger.info("Closing database connections...")

    # Close PostgreSQL engine
    try:
        postgres_engine.dispose()
        logger.info("✅ PostgreSQL connection pool disposed")
    except Exception as e:
        logger.error(f"❌ PostgreSQL dispose error: {e}")

    if mongodb_client:
        try:
            mongodb_client.close()
            logger.info("✅ MongoDB closed")
        except Exception as e:
            logger.error(f"❌ MongoDB close error: {e}")

    if redis_client:
        await redis_client.close()
        logger.info("✅ Redis closed")

    logger.info("Database shutdown complete")


# --- Advanced Cache Manager ---

def _pydantic_serializer(obj: Any) -> str:
    if isinstance(obj, list):
        return json.dumps([item.dict() if isinstance(item, BaseModel) else item for item in obj])
    if isinstance(obj, BaseModel):
        return obj.json()
    return json.dumps(obj)

class CacheManager:
    """Advanced Redis cache manager with Pydantic support and a decorator."""

    @staticmethod
    async def get(key: str, return_type: Optional[Type] = None) -> Any:
        if not redis_client:
            return None
        try:
            data = await redis_client.get(key)
            if data is None:
                return None
            
            if _pydantic_installed and return_type:
                # Check if return_type is a list of Pydantic models
                if hasattr(return_type, '__origin__') and return_type.__origin__ in (list, list) and hasattr(return_type, '__args__'):
                    model_class = return_type.__args__[0]
                    if issubclass(model_class, BaseModel):
                        items = json.loads(data)
                        return [model_class.parse_obj(item) for item in items]

                if issubclass(return_type, BaseModel):
                    return return_type.parse_raw(data)
            
            return json.loads(data)
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return None

    @staticmethod
    async def set(key: str, value: Any, ttl: int = 300) -> bool:
        if not redis_client:
            return False
        try:
            serialized_value = _pydantic_serializer(value)
            await redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False

    @staticmethod
    async def delete(key: str) -> bool:
        if not redis_client:
            return False
        try:
            await redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False

    @staticmethod
    async def clear_pattern(pattern: str) -> int:
        if not redis_client:
            return 0
        try:
            keys = await redis_client.keys(pattern)
            if keys:
                return await redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear error for pattern '{pattern}': {e}")
            return 0

    @classmethod
    def cached(cls, prefix: str = "cache", ttl: int = 300):
        """Decorator to cache the result of an async function."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate a cache key based on function name, args, and kwargs
                sig = inspect.signature(func)
                func_name = func.__name__
                
                # Get the return type annotation for smart deserialization
                return_type = sig.return_type if sig.return_type is not inspect.Signature.empty else None

                # Create a stable key from arguments
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                arg_str = json.dumps(bound_args.arguments, sort_keys=True, default=str)
                
                cache_key = f"{prefix}:{func_name}:{hash(arg_str)}"

                # Try to get from cache
                cached_result = await cls.get(cache_key, return_type)
                if cached_result is not None:
                    logger.debug(f"Cache HIT for key: {cache_key}")
                    return cached_result

                logger.debug(f"Cache MISS for key: {cache_key}")
                # If not in cache, call the function
                result = await func(*args, **kwargs)

                # Store the result in cache
                await cls.set(cache_key, result, ttl)

                return result
            return wrapper
        return decorator
