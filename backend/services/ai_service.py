"""
AI Service for Email Categorization
Handles communication with AI providers (OpenAI, Gemini) for email categorization.
"""

import os
import logging
import time
from typing import Dict, List, Optional, Any
import openai
import google.generativeai as genai
from datetime import datetime

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered email categorization."""

    def __init__(self):
        """Initialize AI service with configured providers."""
        self.openai_client = None
        self.gemini_model = None
        self.default_provider = os.getenv('DEFAULT_AI_PROVIDER', 'openai')
        self.timeout = int(os.getenv('CATEGORIZATION_TIMEOUT', 30))

        # Initialize OpenAI if configured
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self.openai_client = openai.OpenAI(api_key=openai_key)
            logger.info("OpenAI client initialized")

        # Initialize Gemini if configured
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini_model = genai.GenerativeModel(os.getenv('GEMINI_MODEL', 'gemini-pro'))
            logger.info("Gemini client initialized")

        # Define available categories
        self.categories = [
            'Work',
            'Personal',
            'Important',
            'Newsletter',
            'Social',
            'Finance',
            'Shopping',
            'Travel',
            'Health',
            'Education',
            'Entertainment',
            'Spam'
        ]

        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_categorizations': 0,
            'failed_requests': 0,
            'average_response_time': 0
        }

    def categorize_email(self, email_data: Dict[str, Any]) -> str:
        """
        Categorize an email based on its content.

        Args:
            email_data: Dictionary containing email information

        Returns:
            str: Predicted category for the email
        """
        start_time = time.time()

        try:
            self.stats['total_requests'] += 1

            # Create prompt for AI
            prompt = self._create_categorization_prompt(email_data)

            # Get categorization from AI provider
            category = self._get_ai_categorization(prompt)

            if category:
                self.stats['successful_categorizations'] += 1
                response_time = time.time() - start_time
                self._update_response_time(response_time)
                logger.info(f"Email categorized as '{category}' in {response_time:.2f}s")
                return category
            else:
                self.stats['failed_requests'] += 1
                logger.warning("AI categorization failed, returning default category")
                return 'Personal'  # Default fallback

        except Exception as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Error categorizing email: {str(e)}")
            return 'Personal'  # Default fallback

    def _create_categorization_prompt(self, email_data: Dict[str, Any]) -> str:
        """Create a prompt for the AI to categorize the email."""
        subject = email_data.get('subject', '')
        sender = email_data.get('sender', '')
        body = email_data.get('body', '')[:2000]  # Limit body length
        snippet = email_data.get('snippet', '')

        categories_str = ', '.join(self.categories)

        prompt = f"""Analyze this email and categorize it into one of these categories: {categories_str}

Email Details:
- Subject: {subject}
- From: {sender}
- Content: {body or snippet}

Consider the sender, subject line, and content to determine the most appropriate category.
Respond with only the category name, nothing else."""

        return prompt

    def _get_ai_categorization(self, prompt: str) -> Optional[str]:
        """Get categorization from the configured AI provider."""
        try:
            if self.default_provider == 'openai' and self.openai_client:
                return self._categorize_with_openai(prompt)
            elif self.default_provider == 'gemini' and self.gemini_model:
                return self._categorize_with_gemini(prompt)
            else:
                logger.warning(f"Default AI provider '{self.default_provider}' not available")
                # Try fallback provider
                if self.openai_client:
                    return self._categorize_with_openai(prompt)
                elif self.gemini_model:
                    return self._categorize_with_gemini(prompt)
                else:
                    logger.error("No AI providers available")
                    return None
        except Exception as e:
            logger.error(f"Error getting AI categorization: {str(e)}")
            return None

    def _categorize_with_openai(self, prompt: str) -> Optional[str]:
        """Categorize using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.3,
                timeout=self.timeout
            )

            category = response.choices[0].message.content.strip()

            # Validate category
            if category in self.categories:
                return category
            else:
                logger.warning(f"OpenAI returned invalid category: {category}")
                return None

        except Exception as e:
            logger.error(f"OpenAI categorization error: {str(e)}")
            return None

    def _categorize_with_gemini(self, prompt: str) -> Optional[str]:
        """Categorize using Google Gemini."""
        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=50
                )
            )

            category = response.text.strip()

            # Validate category
            if category in self.categories:
                return category
            else:
                logger.warning(f"Gemini returned invalid category: {category}")
                return None

        except Exception as e:
            logger.error(f"Gemini categorization error: {str(e)}")
            return None

    def _update_response_time(self, response_time: float):
        """Update average response time statistic."""
        total_requests = self.stats['successful_categorizations']
        current_avg = self.stats['average_response_time']

        # Calculate new average
        self.stats['average_response_time'] = (
            (current_avg * (total_requests - 1)) + response_time
        ) / total_requests

    def get_available_categories(self) -> List[str]:
        """Get list of available categories."""
        return self.categories.copy()

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            **self.stats,
            'timestamp': self.get_timestamp(),
            'providers': {
                'openai': self.openai_client is not None,
                'gemini': self.gemini_model is not None,
                'default': self.default_provider
            }
        }

    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat()
