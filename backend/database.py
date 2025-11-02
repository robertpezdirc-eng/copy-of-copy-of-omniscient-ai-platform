"""
Database Configuration & Connection Management
Supports: PostgreSQL, MySQL, MongoDB, Redis, Firestore
"""

import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

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
    """
    Dependency for getting database session
    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_mongodb():
    """Get MongoDB database"""
    return mongodb_db


async def get_redis():
    """Get Redis client"""
    return redis_client


def get_firestore():
    """Get Firestore client"""
    return firestore_client


async def init_databases():
    """Initialize all database connections"""
    global mongodb_client, mongodb_db, redis_client, firestore_client

    logger.info("Initializing database connections...")

    # PostgreSQL
    try:
        # Ensure models are imported before create_all so tables are registered
        try:
            from models import gdpr as _gdpr_models  # noqa: F401
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
    """Close all database connections"""
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


# Cache utilities
class CacheManager:
    """Redis cache manager"""

    @staticmethod
    async def get(key: str) -> Optional[str]:
        """Get value from cache"""
        if not redis_client:
            return None
        try:
            return await redis_client.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    @staticmethod
    async def set(key: str, value: str, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        if not redis_client:
            return False
        try:
            await redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    @staticmethod
    async def delete(key: str) -> bool:
        """Delete key from cache"""
        if not redis_client:
            return False
        try:
            await redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    @staticmethod
    async def clear_pattern(pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not redis_client:
            return 0
        try:
            keys = await redis_client.keys(pattern)
            if keys:
                return await redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
