import os
import json
import logging
from http.server import BaseHTTPRequestHandler
from services.ai_service import AIService
from services.gmail_parser import GmailParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
ai_service = AIService()
gmail_parser = GmailParser()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests."""
        try:
            if self.path == '/health':
                self._send_response(200, {
                    'status': 'healthy',
                    'service': 'email-ai-categorizer-backend'
                })
            elif self.path == '/categories':
                categories = ai_service.get_available_categories()
                self._send_response(200, {'categories': categories})
            elif self.path == '/stats':
                stats = ai_service.get_stats()
                self._send_response(200, stats)
            else:
                self._send_response(404, {'error': 'Endpoint not found'})
        except Exception as e:
            logger.error(f'Error in GET request: {str(e)}')
            self._send_response(500, {'error': 'Internal server error'})

    def do_POST(self):
        """Handle POST requests."""
        try:
            if self.path == '/categorize':
                self._handle_categorize()
            else:
                self._send_response(404, {'error': 'Endpoint not found'})
        except Exception as e:
            logger.error(f'Error in POST request: {str(e)}')
            self._send_response(500, {'error': 'Internal server error'})

    def _handle_categorize(self):
        """Handle email categorization requests."""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            if not data:
                self._send_response(400, {'error': 'No data provided'})
                return

            # Validate required fields
            required_fields = ['subject', 'sender']
            for field in required_fields:
                if field not in data:
                    self._send_response(400, {'error': f'Missing required field: {field}'})
                    return

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

            self._send_response(200, {
                'category': category,
                'confidence': 0.85,  # Placeholder confidence score
                'processed_at': ai_service.get_timestamp()
            })

        except json.JSONDecodeError:
            self._send_response(400, {'error': 'Invalid JSON'})
        except Exception as e:
            logger.error(f'Error categorizing email: {str(e)}')
            self._send_response(500, {'error': 'Internal server error'})

    def _send_response(self, status_code, data):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
