import os
import logging
import re
from typing import Dict, Any
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

class AIService:
    def __init__(self):
        logger.info("AI service initialized (rule-based fallback)")
        self._initialized = True

    def categorize_email(self, parsed_content: Dict[str, Any]) -> str:
        """
        Categorize email based on parsed content from GmailParser using simple rules.
        """
        # Extract content from parsed data
        subject = parsed_content.get('subject', '').lower()
        body = parsed_content.get('body', '').lower()
        snippet = parsed_content.get('snippet', '').lower()

        # Combine all content for analysis
        content = f"{subject} {body} {snippet}"

        # Simple rule-based categorization (fallback)
        logger.info(f"Categorizing email with subject: {subject[:50]}...")

        # JOB category (highest priority)
        job_keywords = ['job', 'hiring', 'recruiter', 'application', 'interview', 'position', 'career', 'linkedin', 'indeed', 'ziprecruiter']
        if any(keyword in content for keyword in job_keywords):
            logger.info("Categorized as JOB")
            return "JOB"

        # IMPORTANT category
        important_keywords = ['urgent', 'important', 'asap', 'otp', 'verification', 'password', 'security', 'account', 'billing', 'invoice', 'payment', 'due']
        if any(keyword in content for keyword in important_keywords):
            logger.info("Categorized as IMPORTANT")
            return "IMPORTANT"

        # DELETE category
        delete_keywords = ['sale', 'discount', 'offer', 'promotion', 'marketing', 'newsletter', 'spam', 'unsubscribe', 'advertisement']
        if any(keyword in content for keyword in delete_keywords):
            logger.info("Categorized as DELETE")
            return "DELETE"

        # Default to READ
        logger.info("Categorized as READ (default)")
        return "READ"

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