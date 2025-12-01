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
        # Initialize Gemini
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY missing in .env file")
            
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-1.5-flash"

    def categorize_email(self, subject: str, snippet: str) -> Dict[str, Any]:
        """
        Cleans text, sends to Gemini, and returns the category + color logic.
        """
        # 1. Clean the text (Remove signatures, legal junk)
        clean_snippet = clean_email_text(snippet)

        try:
            # 2. Build the Prompt
            prompt = f"""
            {SYSTEM_PROMPT}

            --- EMAIL TO