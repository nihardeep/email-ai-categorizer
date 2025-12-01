import os
import logging
from typing import Dict, Any
from pydantic import BaseModel, Field
from google import genai
from dotenv import load_dotenv
from services.gmail_parser import clean_email_text

# Load environment variables (API Keys)
load_dotenv()
logger = logging.getLogger(__name__)

# --- THE BRAIN'S RULEBOOK ---
SYSTEM_PROMPT = """
You are an intelligent email classification assistant. 
Your task is to analyze emails and categorize them into exactly one of four categories: 'DELETE', 'JOB', 'READ', or 'IMPORTANT'.

--- CLASSIFICATION RULES ---

1. JOB (Category for Folder):
- All job opening related emails or alerts (LinkedIn, Glassdoor, Indeed, ZipRecruiter).
- Recruiter outreach or interview scheduling.
- "New job matches", "Application status", or "Who viewed your profile".

2. IMPORTANT (Do Not Miss):
- **OTPs (One Time Passwords)** and verification codes (CRITICAL: NEVER DELETE THESE).
- Personal emails from real people (not brands/automated).
- Emails with 'urgent', 'action required', or 'due' in the subject.
- Bills, invoices, or payments that are DUE.
- Meeting invitations, calendar updates, or flight/travel tickets.
- Specific financial reports related to MY specific investments.

3. READ (Mark as Read/Archive):
- Transaction notifications (Credit cards, bank accounts, UPI, mutual funds).
- Automated notifications from apps/software (that are not OTPs).
- Standard newsletters (Marketing, Tech, News) that are not 'Important'.
- Delivery updates (Amazon, FedEx, etc.).

4. DELETE (Trash):
- Promotional emails from brands (Sale, Discount, Offers, "Big Billion Days").
- Spam or junk.
- Surveys, feedback requests, or research studies.
- Stock/Crypto market promotions (generic marketing, not my portfolio).

--- INSTRUCTIONS ---
- Check JOB rules first.
- Check IMPORTANT rules second.
- Check DELETE rules third.
- If unsure, default to READ.
"""

# --- STRUCTURED OUTPUT DEFINITION ---
class EmailAction(BaseModel):
    action: str = Field(description="Must be one of: 'DELETE', 'JOB', 'READ', 'IMPORTANT'")
    confidence: float
    reasoning: str = Field(description="Short explanation of which rule was matched")

class AIService:
    def __init__(self):
        # Defer initialization until first use
        self.client = None
        self.model_name = "gemini-1.5-flash"
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of the AI client."""
        if self._initialized:
            return

        try:
            # Initialize Gemini
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                logger.warning("GEMINI_API_KEY not found in environment variables")
                # Try to load from .env file as fallback
                load_dotenv()
                api_key = os.environ.get("GEMINI_API_KEY")

            if not api_key:
                raise ValueError("GEMINI_API_KEY missing from environment variables and .env file")

            self.client = genai.Client(api_key=api_key)
            self._initialized = True
            logger.info("AI service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            self.client = None
            raise

    def categorize_email(self, parsed_content: Dict[str, Any]) -> str:
        """
        Categorize email based on parsed content from GmailParser.
        """
        # Ensure AI client is initialized
        self._ensure_initialized()

        # Extract content from parsed data
        subject = parsed_content.get('subject', '')
        body = parsed_content.get('body', '')
        snippet = parsed_content.get('snippet', '')

        # Use the best available content for categorization
        content_to_analyze = snippet or body or subject

        # 1. Clean the text (Remove signatures, legal junk)
        clean_content = clean_email_text(content_to_analyze)

        try:
            # 2. Build the Prompt
            prompt = f"""
            {SYSTEM_PROMPT}

            --- EMAIL TO ANALYZE ---
            Subject: {subject}
            Content: {clean_content}

            Return only a JSON object with 'action' (one of: DELETE, JOB, READ, IMPORTANT), 'confidence' (0-1), and 'reasoning'.
            """

            # 3. Send to Gemini
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=genai.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=EmailAction
                )
            )

            # 4. Parse response
            result = response.parsed
            if result and hasattr(result, 'action'):
                return result.action

            # Fallback if parsing fails
            return "READ"

        except Exception as e:
            logger.error(f"Error categorizing email: {e}")
            return "READ"  # Safe fallback

    def get_available_categories(self) -> list:
        """Get list of available email categories."""
        return ["DELETE", "JOB", "READ", "IMPORTANT"]

    def get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def get_stats(self) -> Dict[str, Any]:
        """Get categorization statistics."""
        return {
            "total_categorized": 0,  # Placeholder
            "categories_used": self.get_available_categories(),
            "last_updated": self.get_timestamp()
        }