#!/usr/bin/env python3
"""
Quantum API Endpoint for OMNI Platform Backend
Handles quantum module requests from frontend and routes to appropriate AI functions

This module provides:
- REST API endpoints for quantum modules
- Integration with quantum.py interface
- Request validation and error handling
- Performance monitoring and caching
- Rate limiting and security

Author: OMNI Platform Quantum API
Version: 1.0.0
"""

from flask import Flask, request, jsonify
import json
import time
import logging
from datetime import datetime
from functools import wraps
import os
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# ============================================================================
# QUANTUM API CONFIGURATION
# ============================================================================

class QuantumAPIConfig:
    """Configuration for Quantum API"""

    def __init__(self):
        self.api_base = os.getenv("OMNI_API_BASE", "http://127.0.0.1:8002")
        self.debug_mode = os.getenv("DEBUG", "False").lower() == "true"
        self.max_request_size = 50 * 1024 * 1024  # 50MB
        self.rate_limit_per_minute = 60
        self.request_timeout = 120  # seconds

        # Security settings
        self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
        self.require_api_key = os.getenv("REQUIRE_API_KEY", "False").lower() == "true"
        self.api_key = os.getenv("QUANTUM_API_KEY", "omni-quantum-key-2024")

# Global configuration
quantum_config = QuantumAPIConfig()

# ============================================================================
# QUANTUM MODULES REGISTRY
# ============================================================================

QUANTUM_MODULES = {
    "quantum_gaming": {
        "name": "Quantum Gaming",
        "description": "Generate innovative game ideas and mechanics",
        "functions": ["quantum_gaming_idea", "quantum_game_mechanics"],
        "models": ["gemini-2.0-pro", "gemini-2.0-flash"],
        "category": "entertainment"
    },
    "quantum_tourism": {
        "name": "Quantum Tourism",
        "description": "Create amazing travel experiences and plans",
        "functions": ["quantum_tourism_idea", "quantum_cultural_experience"],
        "models": ["gemini-2.0-pro", "gemini-2.0-flash"],
        "category": "travel"
    },
    "quantum_education": {
        "name": "Quantum Education",
        "description": "Generate educational content and lesson plans",
        "functions": ["quantum_educational_content", "quantum_learning_path"],
        "models": ["gemini-2.0-pro"],
        "category": "education"
    },
    "quantum_business": {
        "name": "Quantum Business",
        "description": "Develop business ideas and market analysis",
        "functions": ["quantum_business_idea", "quantum_market_analysis"],
        "models": ["gemini-2.0-pro"],
        "category": "business"
    },
    "quantum_creative": {
        "name": "Quantum Creative",
        "description": "Create stories, poetry, and artistic content",
        "functions": ["quantum_storytelling", "quantum_poetry"],
        "models": ["gemini-2.0-pro"],
        "category": "creative"
    },
    "quantum_health": {
        "name": "Quantum Health",
        "description": "Generate wellness plans and nutrition guides",
        "functions": ["quantum_wellness_plan", "quantum_nutrition_guide"],
        "models": ["gemini-2.0-pro"],
        "category": "health"
    },
    "quantum_technology": {
        "name": "Quantum Technology",
        "description": "Generate code and system architectures",
        "functions": ["quantum_code_generation", "quantum_system_architecture"],
        "models": ["gemini-2.0-pro"],
        "category": "technology"
    }
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_api_key() -> bool:
    """Validate API key if required"""
    if not quantum_config.require_api_key:
        return True

    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    return api_key == quantum_config.api_key

def validate_request_size() -> bool:
    """Validate request size"""
    if request.content_length and request.content_length > quantum_config.max_request_size:
        return False
    return True

def get_client_ip() -> str:
    """Get client IP address"""
    return request.headers.get('X-Forwarded-For', request.remote_addr) or request.remote_addr

def log_request(module: str, prompt: str, start_time: float):
    """Log API request"""
    duration = time.time() - start_time
    ip = get_client_ip()

    logger.info(f"Quantum API Request: module={module}, duration={duration".2f"}s, ip={ip}, prompt_length={len(prompt)}")

# ============================================================================
# DECORATORS
# ============================================================================

def require_auth(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not validate_api_key():
            return jsonify({
                "ok": False,
                "error": "Invalid or missing API key",
                "timestamp": datetime.now().isoformat()
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def validate_request(f):
    """Decorator to validate request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not validate_request_size():
            return jsonify({
                "ok": False,
                "error": "Request too large",
                "timestamp": datetime.now().isoformat()
            }), 413

        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# QUANTUM API ENDPOINTS
# ============================================================================

@app.route('/api/quantum/status', methods=['GET'])
def quantum_status():
    """Get quantum AI interface status"""
    try:
        # Import quantum interface
        from quantum import get_quantum_status

        status = get_quantum_status()
        status.update({
            "api_version": "1.0.0",
            "server_time": datetime.now().isoformat(),
            "uptime": time.time(),  # Would be actual uptime in production
            "available_modules": list(QUANTUM_MODULES.keys())
        })

        return jsonify({
            "ok": True,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })

    except ImportError:
        return jsonify({
            "ok": False,
            "error": "Quantum interface not available",
            "timestamp": datetime.now().isoformat()
        }), 503
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return jsonify({
            "ok": False,
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/quantum/query', methods=['POST'])
@require_auth
@validate_request
def quantum_query():
    """Main quantum query endpoint"""
    start_time = time.time()

    try:
        # Get request data
        data = request.get_json()

        if not data:
            return jsonify({
                "ok": False,
                "error": "No JSON data provided",
                "timestamp": datetime.now().isoformat()
            }), 400

        # Extract parameters
        module = data.get('module')
        prompt = data.get('prompt', '').strip()
        model = data.get('model', 'gemini-2.0-flash')
        options = data.get('options', {})

        # Validate required fields
        if not module:
            return jsonify({
                "ok": False,
                "error": "Module parameter is required",
                "timestamp": datetime.now().isoformat()
            }), 400

        if not prompt:
            return jsonify({
                "ok": False,
                "error": "Prompt parameter is required",
                "timestamp": datetime.now().isoformat()
            }), 400

        # Validate module exists
        if module not in QUANTUM_MODULES:
            return jsonify({
                "ok": False,
                "error": f"Unknown module: {module}",
                "available_modules": list(QUANTUM_MODULES.keys()),
                "timestamp": datetime.now().isoformat()
            }), 400

        # Validate model for module
        module_info = QUANTUM_MODULES[module]
        if model not in module_info['models']:
            return jsonify({
                "ok": False,
                "error": f"Model {model} not supported for module {module}",
                "supported_models": module_info['models'],
                "timestamp": datetime.now().isoformat()
            }), 400

        logger.info(f"Processing quantum query: module={module}, model={model}, prompt_length={len(prompt)}")

        # Route to appropriate quantum function
        result = route_to_quantum_function(module, prompt, model, options)

        # Log request
        log_request(module, prompt, start_time)

        # Return result
        return jsonify({
            "ok": True,
            "module": module,
            "model": model,
            "reply": result,
            "execution_time": time.time() - start_time,
            "timestamp": datetime.now().isoformat()
        })

    except json.JSONDecodeError:
        return jsonify({
            "ok": False,
            "error": "Invalid JSON data",
            "timestamp": datetime.now().isoformat()
        }), 400
    except Exception as e:
        logger.error(f"Quantum query error: {e}")
        return jsonify({
            "ok": False,
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }), 500

def route_to_quantum_function(module: str, prompt: str, model: str, options: Dict) -> str:
    """Route request to appropriate quantum function"""
    try:
        # Import quantum functions
        from quantum import (
            quantum_gaming_idea, quantum_game_mechanics,
            quantum_tourism_idea, quantum_cultural_experience,
            quantum_educational_content, quantum_learning_path,
            quantum_business_idea, quantum_market_analysis,
            quantum_storytelling, quantum_poetry,
            quantum_wellness_plan, quantum_nutrition_guide,
            quantum_code_generation, quantum_system_architecture
        )

        # Route based on module and prompt content
        if module == "quantum_gaming":
            if "mechanics" in prompt.lower() or "mehanike" in prompt.lower():
                return quantum_game_mechanics(prompt)
            else:
                return quantum_gaming_idea(
                    theme=options.get('theme'),
                    age_group=options.get('age_group', 'children'),
                    game_type=options.get('game_type', 'active')
                )

        elif module == "quantum_tourism":
            if "cultural" in prompt.lower() or "kulturna" in prompt.lower():
                return quantum_cultural_experience(
                    location=prompt,
                    interest=options.get('interest', 'history')
                )
            else:
                return quantum_tourism_idea(
                    location=prompt,
                    duration=options.get('duration', 'weekend'),
                    budget=options.get('budget', 'medium')
                )

        elif module == "quantum_education":
            if "path" in prompt.lower() or "načrt" in prompt.lower():
                return quantum_learning_path(
                    skill=prompt,
                    timeframe=options.get('timeframe', '3_months')
                )
            else:
                return quantum_educational_content(
                    topic=prompt,
                    level=options.get('level', 'intermediate'),
                    format_type=options.get('format', 'lesson_plan')
                )

        elif module == "quantum_business":
            if "analysis" in prompt.lower() or "analiza" in prompt.lower():
                return quantum_market_analysis(
                    product=prompt,
                    market=options.get('market', 'slovenia')
                )
            else:
                return quantum_business_idea(
                    industry=prompt,
                    problem=options.get('problem')
                )

        elif module == "quantum_creative":
            if "poetry" in prompt.lower() or "pesem" in prompt.lower():
                return quantum_poetry(
                    theme=prompt,
                    style=options.get('style', 'free_verse'),
                    language=options.get('language', 'slovenian')
                )
            else:
                return quantum_storytelling(
                    prompt=prompt,
                    genre=options.get('genre', 'fantasy'),
                    length=options.get('length', 'short')
                )

        elif module == "quantum_health":
            if "nutrition" in prompt.lower() or "prehrana" in prompt.lower():
                return quantum_nutrition_guide(
                    diet_type=prompt,
                    calories=options.get('calories', 2000),
                    preferences=options.get('preferences')
                )
            else:
                return quantum_wellness_plan(
                    goals=prompt,
                    timeframe=options.get('timeframe', '30_days'),
                    fitness_level=options.get('fitness_level', 'beginner')
                )

        elif module == "quantum_technology":
            if "architecture" in prompt.lower() or "arhitektura" in prompt.lower():
                return quantum_system_architecture(
                    description=prompt,
                    requirements=options.get('requirements', [])
                )
            else:
                return quantum_code_generation(
                    language=options.get('language', 'Python'),
                    specification=prompt,
                    complexity=options.get('complexity', 'intermediate')
                )

        else:
            # Default fallback
            from quantum import call_gemini
            return call_gemini(prompt, model)

    except ImportError as e:
        logger.error(f"Quantum function import error: {e}")
        return f"Error: Quantum module '{module}' not available"
    except Exception as e:
        logger.error(f"Quantum function execution error: {e}")
        return f"Error: Failed to process quantum request - {str(e)}"

@app.route('/api/quantum/modules', methods=['GET'])
def list_quantum_modules():
    """List available quantum modules"""
    try:
        modules_info = {}

        for module_id, module_info in QUANTUM_MODULES.items():
            modules_info[module_id] = {
                "name": module_info["name"],
                "description": module_info["description"],
                "functions": module_info["functions"],
                "models": module_info["models"],
                "category": module_info["category"]
            }

        return jsonify({
            "ok": True,
            "modules": modules_info,
            "total_modules": len(QUANTUM_MODULES),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Modules list error: {e}")
        return jsonify({
            "ok": False,
            "error": "Failed to retrieve modules list",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/quantum/cache/clear', methods=['POST'])
@require_auth
def clear_quantum_cache():
    """Clear quantum AI cache"""
    try:
        from quantum import clear_quantum_cache

        clear_quantum_cache()

        return jsonify({
            "ok": True,
            "message": "Quantum cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        })

    except ImportError:
        return jsonify({
            "ok": False,
            "error": "Quantum interface not available",
            "timestamp": datetime.now().isoformat()
        }), 503
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return jsonify({
            "ok": False,
            "error": "Failed to clear cache",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/quantum/health', methods=['GET'])
def quantum_health():
    """Health check for quantum API"""
    try:
        # Check quantum interface availability
        try:
            from quantum import get_quantum_status
            status = get_quantum_status()
            quantum_available = True
        except ImportError:
            status = {"error": "Quantum interface not available"}
            quantum_available = False

        health_info = {
            "status": "healthy" if quantum_available else "degraded",
            "quantum_available": quantum_available,
            "api_version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time(),
            "quantum_status": status
        }

        status_code = 200 if quantum_available else 503

        return jsonify(health_info), status_code

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "error",
            "error": "Health check failed",
            "timestamp": datetime.now().isoformat()
        }), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "ok": False,
        "error": "Endpoint not found",
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "ok": False,
        "error": "Method not allowed",
        "timestamp": datetime.now().isoformat()
    }), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "ok": False,
        "error": "Internal server error",
        "timestamp": datetime.now().isoformat()
    }), 500

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def create_quantum_api_app():
    """Create and configure the quantum API Flask app"""
    # Configure Flask app
    app.config['MAX_CONTENT_LENGTH'] = quantum_config.max_request_size
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

    # Add CORS headers if needed
    @app.after_request
    def add_cors_headers(response):
        if "*" in quantum_config.allowed_origins or request.headers.get('Origin') in quantum_config.allowed_origins:
            response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-API-Key')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    return app

if __name__ == "__main__":
    print("🚀 Starting OMNI Quantum API Server")
    print("=" * 50)
    print(f"API Base: {quantum_config.api_base}")
    print(f"Debug Mode: {quantum_config.debug_mode}")
    print(f"Max Request Size: {quantum_config.max_request_size // (1024*1024)}MB")
    print(f"Rate Limit: {quantum_config.rate_limit_per_minute}/minute")
    print(f"API Key Required: {quantum_config.require_api_key}")
    print()

    # Create and run app
    quantum_app = create_quantum_api_app()

    print("📡 Available endpoints:")
    print("  GET  /api/quantum/status")
    print("  POST /api/quantum/query")
    print("  GET  /api/quantum/modules")
    print("  POST /api/quantum/cache/clear")
    print("  GET  /api/quantum/health")
    print()

    print("🧠 Quantum modules available:")
    for module_id, module_info in QUANTUM_MODULES.items():
        print(f"  • {module_id}: {module_info['name']}")

    print()
    print("✅ Quantum API server ready!")

    # Run the server
    quantum_app.run(
        host='0.0.0.0',
        port=8002,
        debug=quantum_config.debug_mode,
        threaded=True
    )