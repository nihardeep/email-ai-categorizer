import os
import sys
import json
import logging

print("🐍 Starting Python serverless function...")
print(f"📂 Current working directory: {os.getcwd()}")
print(f"📂 Python path: {sys.path}")

# Add the api directory to Python path so we can import services
api_dir = os.path.dirname(os.path.abspath(__file__))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)
    print(f"📂 Added to Python path: {api_dir}")

try:
    from flask import Flask, request, jsonify
    print("✅ Flask imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Flask: {e}")

try:
    from flask_cors import CORS
    print("✅ Flask-CORS imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Flask-CORS: {e}")

try:
    from ai_service import AIService
    print("✅ AI service imported successfully")
except ImportError as e:
    print(f"❌ Failed to import AI service: {e}")
    import traceback
    print(f"❌ Import traceback: {traceback.format_exc()}")

try:
    from gmail_parser import GmailParser
    print("✅ Gmail parser imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Gmail parser: {e}")
    import traceback
    print(f"❌ Import traceback: {traceback.format_exc()}")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for extension requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
print("🔧 Initializing AI service...")
try:
    ai_service = AIService()
    print("✅ AI service initialized")
except Exception as e:
    print(f"❌ Failed to initialize AI service: {e}")
    ai_service = None

print("🔧 Initializing Gmail parser...")
try:
    gmail_parser = GmailParser()
    print("✅ Gmail parser initialized")
except Exception as e:
    print(f"❌ Failed to initialize Gmail parser: {e}")
    gmail_parser = None

@app.route('/', methods=['GET'])
def root():
    """Root endpoint."""
    print("🏠 Root endpoint called")
    return jsonify({
        'message': 'Email AI Categorizer API',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'categorize': '/categorize (POST)',
            'categories': '/categories'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    print("🏥 Health check called")
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
    print("📧 Categorize endpoint called")
    try:
        print("📨 Getting JSON data...")
        data = request.get_json()
        print(f"📨 Received data: {data}")

        if not data:
            print("❌ No data provided")
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['subject', 'sender']
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing required field: {field}")
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Extract email content
        subject = data.get('subject', '')
        sender = data.get('sender', '')
        body = data.get('body', '')
        snippet = data.get('snippet', '')

        print(f"📧 Processing email: {subject} from {sender}")

        # Parse and clean email content
        print("🔍 Parsing email content...")
        parsed_content = gmail_parser.parse_email(subject, sender, body, snippet)

        # Get category from AI service
        print("🤖 Getting category from AI service...")
        category = ai_service.categorize_email(parsed_content)

        print(f"✅ Categorized email as: {category}")

        logger.info(f'Categorized email "{subject}" as "{category}"')

        return jsonify({
            'category': category,
            'confidence': 0.85,  # Placeholder confidence score
            'processed_at': ai_service.get_timestamp()
        })

    except Exception as e:
        print(f"❌ Error in categorize_email: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
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

# For Vercel deployment, just export the Flask app
# Vercel automatically handles WSGI applications
print("🚀 Starting Flask app for Vercel deployment...")
print(f"📍 Available routes: {[rule.rule for rule in app.url_map.iter_rules()]}")
