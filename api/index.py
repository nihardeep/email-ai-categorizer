import os
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from services.ai_service import AIService
from services.gmail_parser import GmailParser

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for extension requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
ai_service = AIService()
gmail_parser = GmailParser()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'email-ai-categorizer-backend'
    })

@app.route('/categorize', methods=['POST'])
def categorize_email():
    """
    Categorize an email based on its content.

    Expected JSON payload:
    {
        "subject": "Email subject",
        "sender": "sender@example.com",
        "body": "Email body content...",
        "snippet": "Email preview snippet (optional)"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['subject', 'sender']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Extract email content
        subject = data.get('subject', '')
        sender = data.get('sender', '')
        body = data.get('body', '')
        snippet = data.get('snippet', '')

        # Parse and clean email content
        parsed_content = gmail_parser.parse_email(subject, sender, body, snippet)

        # Get category from AI service
        category = ai_service.categorize_email(parsed_content)

        logger.info(f'Categorized email "{subject}" as "{category}"')

        return jsonify({
            'category': category,
            'confidence': 0.85,  # Placeholder confidence score
            'processed_at': ai_service.get_timestamp()
        })

    except Exception as e:
        logger.error(f'Error categorizing email: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/categories', methods=['GET'])
def get_categories():
    """Get available email categories."""
    try:
        categories = ai_service.get_available_categories()
        return jsonify({
            'categories': categories
        })
    except Exception as e:
        logger.error(f'Error getting categories: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get categorization statistics."""
    try:
        stats = ai_service.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f'Error getting stats: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Vercel serverless function handler
def handler(event, context):
    """
    Vercel serverless function handler.
    This function wraps the Flask app for Vercel deployment.
    """
    from werkzeug.test import Client
    from werkzeug.wrappers import Response

    # Create a test client
    client = Client(app)

    # Extract request details from Vercel event
    method = event.get('method', 'GET')
    path = event.get('path', '/')
    headers = event.get('headers', {})
    body = event.get('body', '')

    # Convert headers to werkzeug format
    werkzeug_headers = []
    for key, value in headers.items():
        werkzeug_headers.append((key, value))

    # Make the request
    response = client.open(path, method=method, headers=werkzeug_headers, data=body)

    # Return response in Vercel format
    return {
        'statusCode': response.status_code,
        'headers': dict(response.headers),
        'body': response.get_data(as_text=True)
    }
