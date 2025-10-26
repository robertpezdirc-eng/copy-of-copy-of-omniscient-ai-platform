#!/usr/bin/env python3
"""
OMNI Platform - Google Cloud Function
Serverless deployment for OMNI AI platform
"""

import os
import json
import logging
from datetime import datetime
import functions_framework
import google.generativeai as genai
from google.cloud import storage, pubsub_v1, logging as cloud_logging

# Configure logging
cloud_logging.Client().setup_logging()
logger = logging.getLogger(__name__)

# Google Cloud configuration
PROJECT_ID = os.environ.get('PROJECT_ID', 'gen-lang-client-0885737339')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')

# Initialize Google Generative AI
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel(GEMINI_MODEL)

# Initialize Cloud Storage
storage_client = storage.Client()
bucket_name = f'omni-platform-storage-{PROJECT_ID}'

# Initialize Pub/Sub
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, 'omni-workflows')

class OmniCloudFunction:
    def __init__(self):
        self.system_prompt = """Ti si OMNI Cloud Function AI, napredni AI asistent na Google Cloud Platform.

        Funkcije:
        - Inteligentno odgovarjanje v slovenščini
        - Uporaba Google Gemini AI za analize
        - Shranjevanje podatkov v Google Cloud Storage
        - Publikacija sporočil v Pub/Sub
        - Serverless deployment

        Vedno odgovarjaj v slovenščini in bodi maksimalno pomočni."""

    def process_query(self, query, user_id='default'):
        try:
            # Generate response using Gemini
            response = model.generate_content(
                f"{self.system_prompt}\n\nUporabnik: {query}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1000,
                )
            )

            result = {
                'success': True,
                'response': response.text,
                'used_ai': 'gemini',
                'platform': 'google-cloud-function',
                'deployment': 'serverless',
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'project_id': PROJECT_ID
            }

            # Save to Cloud Storage
            self.save_to_storage(user_id, query, result)

            # Publish to Pub/Sub for workflow processing
            self.publish_to_pubsub(query, user_id)

            return result

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'success': False,
                'error': 'Napaka pri procesiranju',
                'message': str(e),
                'platform': 'google-cloud-function'
            }

    def save_to_storage(self, user_id, query, result):
        """Save conversation to Google Cloud Storage"""
        try:
            bucket = storage_client.bucket(bucket_name)
            filename = f"conversations/{user_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

            blob = bucket.blob(filename)
            blob.upload_string(json.dumps({
                'query': query,
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            }, ensure_ascii=False, indent=2))

            logger.info(f"Saved conversation to {filename}")

        except Exception as e:
            logger.error(f"Error saving to storage: {e}")

    def publish_to_pubsub(self, query, user_id):
        """Publish message to Pub/Sub for workflow processing"""
        try:
            message_data = json.dumps({
                'query': query,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'omni-cloud-function'
            }, ensure_ascii=False).encode('utf-8')

            future = publisher.publish(topic_path, message_data)
            message_id = future.result()

            logger.info(f"Published message {message_id} to {topic_path}")

        except Exception as e:
            logger.error(f"Error publishing to Pub/Sub: {e}")

# Initialize OMNI Cloud Function
omni_function = OmniCloudFunction()

@functions_framework.http
def omni_chat(request):
    """Main chat function"""
    try:
        # Handle CORS
        if request.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type',
            }
            return ('', 204, headers)

        # Only allow POST requests
        if request.method != 'POST':
            return jsonify({'error': 'Method not allowed'}), 405

        # Get request data
        request_json = request.get_json(silent=True)

        if not request_json or 'message' not in request_json:
            return jsonify({
                'success': False,
                'error': 'Sporočilo je obvezno'
            }), 400

        message = request_json['message']
        user_id = request_json.get('user_id', 'default')

        logger.info(f"Processing chat message: {message[:50]}...")

        result = omni_function.process_query(message, user_id)

        # Add CORS headers to response
        headers = {'Access-Control-Allow-Origin': '*'}

        return jsonify(result), 200, headers

    except Exception as e:
        logger.error(f"Function error: {e}")
        headers = {'Access-Control-Allow-Origin': '*'}
        return jsonify({
            'success': False,
            'error': 'Notranja napaka',
            'message': str(e)
        }), 500, headers

@functions_framework.http
def omni_status(request):
    """Status function"""
    try:
        return jsonify({
            'status': 'active',
            'platform': 'omni-cloud-function',
            'provider': 'google-cloud',
            'deployment': 'serverless',
            'project_id': PROJECT_ID,
            'gemini_model': GEMINI_MODEL,
            'services': {
                'gemini': 'active',
                'cloud_storage': 'active',
                'pubsub': 'active',
                'cloud_functions': 'active'
            },
            'features': [
                'AI Chat (Gemini)',
                'Cloud Storage',
                'Pub/Sub Integration',
                'Serverless Deployment',
                'CORS Support'
            ],
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@functions_framework.http
def omni_health(request):
    """Health check function"""
    try:
        return jsonify({
            'status': 'healthy',
            'platform': 'google-cloud-function',
            'deployment': 'serverless',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'gemini_api': 'ok',
                'cloud_storage': 'ok',
                'pubsub': 'ok'
            }
        })

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500