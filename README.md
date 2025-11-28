# Email AI Categorizer

A Chrome extension that automatically categorizes your Gmail emails using AI.

## Features

- Automatically analyzes incoming emails
- Categorizes emails based on content and context
- Integrates seamlessly with Gmail interface
- Uses advanced AI models for accurate categorization

## Installation

### Prerequisites

- Google Chrome browser
- Python 3.8 or higher
- OpenAI API key (or Gemini API key)

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/email-ai-categorizer.git
   cd email-ai-categorizer
   ```

2. **Backend Setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Environment Configuration:**
   - Copy `.env.example` to `.env`
   - Add your API keys to `.env`:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     GEMINI_API_KEY=your_gemini_api_key_here
     ```

4. **Start the backend server:**
   ```bash
   python app.py
   ```

5. **Extension Installation:**
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" (top right)
   - Click "Load unpacked"
   - Select the `extension` folder from this project

## Usage

1. Click the extension icon in Chrome toolbar
2. The extension will automatically run on Gmail pages
3. Emails will be automatically categorized as they arrive

## Development

### Project Structure

```
email-ai-categorizer/
├── extension/          # Chrome extension files
├── backend/           # Python Flask server
└── README.md         # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Privacy

This extension processes email content locally and communicates with your backend server. No email data is sent to third-party services except for the AI API you configure.
