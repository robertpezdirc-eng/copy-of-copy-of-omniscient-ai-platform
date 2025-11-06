"""
Celery Tasks Module

This module defines all the asynchronous tasks that will be executed by Celery workers.
Tasks can be related to sending emails, processing data, training ML models, etc.
"""

import time
import logging
from .celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.send_email_task")
def send_email_task(recipient: str, subject: str, body: str):
    """
    A mock task that simulates sending an email.

    In a real application, this would use a service like SendGrid or SMTP to
    dispatch the email.
    """
    logger.info(f"Sending email to: {recipient} with subject: '{subject}'")
    
    # Simulate a network delay or a long-running operation
    time.sleep(5)  # Simulate 5 seconds of work
    
    # Simulate a successful completion
    result = {"status": "success", "recipient": recipient, "subject": subject}
    logger.info(f"Email sent successfully to {recipient}.")
    
    return result


@celery_app.task(name="tasks.long_running_ml_task")
def long_running_ml_task(model_id: str, training_data_path: str):
    """
    A mock task for a long-running machine learning model training job.
    """
    logger.info(f"Starting ML training for model: {model_id} with data from {training_data_path}")
    
    # Simulate a very long task
    time.sleep(300)  # Simulate 5 minutes of training
    
    accuracy = 0.95  # Mock accuracy
    result = {"status": "completed", "model_id": model_id, "accuracy": accuracy}
    
    logger.info(f"ML training for model {model_id} completed with accuracy {accuracy}.")
    return result

# To add more tasks, simply define them here with the @celery_app.task decorator.
# Example of a high-priority task:
# @celery_app.task(queue='high_priority')
# def high_priority_task():
#     ...
