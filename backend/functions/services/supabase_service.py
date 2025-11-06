"""
Supabase Service
Handles all interactions with the Supabase backend.
"""

import os
from supabase_async import create_client, AsyncClient
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

_client: AsyncClient = None

async def get_supabase_client() -> AsyncClient:
    """
    Returns an initialized Supabase client. Caches the client for reuse.
    
    Raises:
        ValueError: If Supabase URL or anon key are not set.
        
    Returns:
        An initialized Supabase client.
    """
    global _client
    if _client:
        return _client

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_anon_key:
        logger.error("Supabase credentials are not set in environment variables.")
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set.")

    try:
        _client = await create_client(supabase_url, supabase_anon_key)
        logger.info("Supabase client initialized successfully.")
        return _client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise
