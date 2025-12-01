"""
Gmail Parser Service
Handles parsing and cleaning of Gmail content for AI processing.
"""

import re
import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import html

logger = logging.getLogger(__name__)

class GmailParser:
    """Service for parsing and cleaning Gmail content."""

    def __init__(self):
        """Initialize the Gmail parser."""
        # Common email signatures and footers to remove
        self.signature_patterns = [
            r'--\s*$',  # Simple signature separator
            r'Best regards,.*',
            r'Regards,.*',
            r'Cheers,.*',
            r'Thank you,.*',
            r'Sent from.*',
            r'Confidential.*',
            r'This email.*',
        ]

        # Patterns for promotional content
        self.promotional_patterns = [
            r'unsubscribe.*',
            r'click here to unsubscribe',
            r'privacy policy.*',
            r'terms of service.*',
            r'© \d{4}.*',
        ]

    def parse_email(self, subject: str, sender: str, body: str = '', snippet: str = '') -> Dict[str, Any]:
        """
        Parse and clean email content.

        Args:
            subject: Email subject line
            sender: Email sender address
            body: Email body content (HTML or plain text)
            snippet: Email preview snippet

        Returns:
            Dict containing cleaned and parsed email data
        """
        try:
            # Clean subject
            clean_subject = self._clean_subject(subject)

            # Clean sender
            clean_sender = self._clean_sender(sender)

            # Clean and extract body content
            clean_body = self._clean_body(body)

            # Use snippet if body is empty
            if not clean_body and snippet:
                clean_body = snippet

            # Extract additional features
            features = self._extract_features(clean_subject, clean_sender, clean_body)

            return {
                'subject': clean_subject,
                'sender': clean_sender,
                'body': clean_body,
                'features': features,
                'is_promotional': self._is_promotional(clean_subject, clean_body),
                'priority_score': self._calculate_priority_score(features)
            }

        except Exception as e:
            logger.error(f"Error parsing email: {str(e)}")
            return {
                'subject': subject,
                'sender': sender,
                'body': body or snippet,
                'features': {},
                'is_promotional': False,
                'priority_score': 0
            }

    def _clean_subject(self, subject: str) -> str:
        """Clean and normalize email subject."""
        if not subject:
            return ''

        # Remove common prefixes
        subject = re.sub(r'^(Re|Fwd|FW|RE|FWD):\s*', '', subject, flags=re.IGNORECASE)

        # Remove extra whitespace
        subject = ' '.join(subject.split())

        # Decode HTML entities
        subject = html.unescape(subject)

        return subject.strip()

    def _clean_sender(self, sender: str) -> str:
        """Clean and normalize sender email address."""
        if not sender:
            return ''

        # Extract email from "Name <email>" format
        email_match = re.search(r'<([^>]+)>', sender)
        if email_match:
            return email_match.group(1).strip().lower()

        # Clean up email address
        sender = sender.strip().lower()

        # Remove any remaining angle brackets
        sender = re.sub(r'[<>]', '', sender)

        return sender

    def _clean_body(self, body: str) -> str:
        """Clean email body content."""
        if not body:
            return ''

        try:
            # Try to parse as HTML
            soup = BeautifulSoup(body, 'html.parser')

            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()

            # Extract text
            text = soup.get_text()

        except:
            # If HTML parsing fails, treat as plain text
            text = body

        # Decode HTML entities
        text = html.unescape(text)

        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single

        # Remove common email signatures and footers
        for pattern in self.signature_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)

        # Limit length to prevent token overflow
        max_length = int(os.getenv('MAX_EMAIL_LENGTH', 10000))
        if len(text) > max_length:
            text = text[:max_length] + '...'

        return text.strip()

    def _extract_features(self, subject: str, sender: str, body: str) -> Dict[str, Any]:
        """Extract useful features from email content."""
        features = {}

        # Subject features
        features['subject_length'] = len(subject)
        features['has_urgent'] = bool(re.search(r'urgent|important|asap|emergency', subject + body, re.IGNORECASE))
        features['has_question'] = '?' in subject or '?' in body
        features['is_reply'] = subject.lower().startswith(('re:', 'fwd:', 'fw:'))

        # Sender features
        features['sender_domain'] = sender.split('@')[-1] if '@' in sender else ''
        features['is_common_domain'] = features['sender_domain'] in [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com'
        ]

        # Body features
        features['body_length'] = len(body)
        features['has_links'] = bool(re.search(r'http[s]?://', body))
        features['has_attachments'] = bool(re.search(r'attachment|attached', body, re.IGNORECASE))

        # Content analysis
        features['contains_money'] = bool(re.search(r'\$[\d,]+|\b\d+\s*(?:dollars?|usd|eur|gbp)', body, re.IGNORECASE))
        features['contains_dates'] = bool(re.search(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', body, re.IGNORECASE))

        return features

    def _is_promotional(self, subject: str, body: str) -> bool:
        """Determine if email appears to be promotional."""
        content = (subject + ' ' + body).lower()

        # Check for promotional patterns
        for pattern in self.promotional_patterns:
            if re.search(pattern, content):
                return True

        # Check for common promotional words
        promotional_words = ['deal', 'offer', 'discount', 'sale', 'free', 'buy now', 'limited time']
        word_count = sum(1 for word in promotional_words if word in content)

        return word_count >= 2

    def _calculate_priority_score(self, features: Dict[str, Any]) -> float:
        """Calculate a priority score based on email features."""
        score = 0.0

        # Urgent keywords
        if features.get('has_urgent', False):
            score += 0.3

        # Questions (might need response)
        if features.get('has_question', False):
            score += 0.2

        # Money-related
        if features.get('contains_money', False):
            score += 0.2

        # Short subject (might be important)
        if features.get('subject_length', 0) < 50:
            score += 0.1

        # From known domain
        if features.get('is_common_domain', False):
            score -= 0.1

        # Clamp score between 0 and 1
        return max(0.0, min(1.0, score))


# Standalone function for AI service (backward compatibility)
def clean_email_text(text: str) -> str:
    """
    Clean email text for AI processing.
    This is a standalone function that can be imported by ai_service.
    """
    if not text:
        return ''

    try:
        # Try to parse as HTML
        soup = BeautifulSoup(text, 'html.parser')

        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()

        # Extract text
        cleaned_text = soup.get_text()

    except:
        # If HTML parsing fails, treat as plain text
        cleaned_text = text

    # Decode HTML entities
    cleaned_text = html.unescape(cleaned_text)

    # Remove excessive whitespace
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)  # Multiple newlines to double
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)  # Multiple spaces to single

    # Remove common email signatures and footers
    signature_patterns = [
        r'--\s*$',  # Simple signature separator
        r'Best regards,.*',
        r'Regards,.*',
        r'Cheers,.*',
        r'Thank you,.*',
        r'Sent from.*',
        r'Confidential.*',
        r'This email.*',
    ]

    for pattern in signature_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)

    # Limit length to prevent token overflow
    import os
    max_length = int(os.getenv('MAX_EMAIL_LENGTH', 10000))
    if len(cleaned_text) > max_length:
        cleaned_text = cleaned_text[:max_length] + '...'

    return cleaned_text.strip()
