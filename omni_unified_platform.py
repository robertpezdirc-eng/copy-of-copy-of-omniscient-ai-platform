#!/usr/bin/env python3
"""
OMNI Unified Platform Entry Point
==================================
Entry point for the OMNI Unified Platform backend service.
This module imports and runs the FastAPI application from backend/main.py
with proper configuration for Cloud Run deployment.
"""

import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def main():
    """Main entry point for the OMNI Unified Platform."""
    try:
        import uvicorn
        from main import app
    except ImportError as e:
        print(f"ERROR: Failed to import required modules: {e}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Python path: {sys.path}")
        print(f"Backend directory exists: {os.path.exists('backend')}")
        if os.path.exists('backend'):
            print(f"Backend contents: {os.listdir('backend')}")
        sys.exit(1)
    
    # Get port from environment variable (Cloud Run sets PORT=8080)
    port = int(os.environ.get("PORT", "8080"))
    host = os.environ.get("HOST", "0.0.0.0")
    
    # Log startup information
    print(f"Starting OMNI Unified Platform on {host}:{port}")
    print(f"Environment: {os.environ.get('GOOGLE_CLOUD_PROJECT', 'local')}")
    
    # Run the application with uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=os.environ.get("LOG_LEVEL", "info").lower(),
        access_log=True
    )

if __name__ == "__main__":
    main()
