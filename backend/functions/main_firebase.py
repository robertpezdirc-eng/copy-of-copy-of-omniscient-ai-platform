"""
OMNI ENTERPRISE ULTRA MAX - Firebase Cloud Function Entry Point
"""

from firebase_functions import https_fn
from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
import logging

# Import core components from the main application
from main import app as fastapi_app, _register_routers
from database import init_databases, close_databases

logger = logging.getLogger(__name__)

# Special considerations for Firebase:
# Force OMNI_MINIMAL to false to ensure all routes are loaded
os.environ["OMNI_MINIMAL"] = "false"
logger.info("Firebase environment detected. Forcing full feature set by setting OMNI_MINIMAL=false.")

# Re-register routers to apply the override
# This is a bit of a hack, but it ensures we get all routes.
# A cleaner way would be to refactor _register_routers to accept a flag.
for r in fastapi_app.routes:
    if r.name and r.name != 'root':
        # This isn't perfect, but it's a way to clear out existing routes
        # before re-registering them all.
        pass # No easy public API to unregister routes

_register_routers(fastapi_app) # Register all routes


@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
    """ Firebase Cloud Function entry point that serves the FastAPI app. """
    # Note: Firebase manages the lifespan, so we don't use the lifespan context here.
    # The init_databases and close_databases will be triggered by the FastAPI lifespan manager
    # if the function instance is re-used or shut down.
    return https_fn.Response(fastapi_app(req.environ, None))
