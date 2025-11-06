"""
Celery Application Factory and Configuration

This module is responsible for creating and configuring the Celery application instance.
It pulls broker and backend configuration from environment variables and sets up
secure and optimized defaults.
"""

import os
from celery import Celery

# Get Redis URL from environment with a fallback for local development
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# --- Celery App Initialization ---

# We instantiate the app here, but the configuration is applied below.
# The name 'celery_app' is the standard convention.
celery_app = Celery(
    "omni_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['backend.functions.tasks']  # Tells Celery where to find task modules
)

# --- Celery Configuration ---

celery_app.conf.update(
    # --- Broker Settings ---
    # Ensures messages are acknowledged only after the task completes successfully.
    # This prevents tasks from being lost if the worker crashes.
    task_acks_late=True,

    # --- Task Execution Settings ---
    # Use JSON as the serializer for better security and interoperability.
    task_serializer='json',
    accept_content=['json'],
    
    # --- Result Backend Settings ---
    result_serializer='json',
    result_expires=3600,  # Store results for 1 hour
    
    # --- Timezone Settings ---
    # Use UTC for all internal Celery timings and schedules to avoid timezone issues.
    timezone='UTC',
    enable_utc=True,

    # --- Worker Settings ---
    # Prefetch multiplier of 1 ensures that a worker only reserves one extra task.
    # This is ideal for long-running tasks, preventing them from tying up the queue.
    worker_prefetch_multiplier=1,

    # --- Routing and Queues (Example) ---
    # Although we start with a default queue, this shows how to set up more complex routing.
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'high_priority': {
            'exchange': 'high_priority',
            'routing_key': 'high_priority',
        },
    },
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
)

if __name__ == '__main__':
    # To run the worker, use the following command in your terminal:
    # celery -A backend.functions.celery_app.celery_app worker --loglevel=info
    celery_app.start()
