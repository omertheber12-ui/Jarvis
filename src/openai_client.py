"""
OpenAI API client - handles communication with OpenAI API
"""

from openai import OpenAI
from .config import OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_API_KEY


class OpenAIClient:
    """Handles communication with OpenAI API"""
    
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set. Please check your .env file or environment variables.")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        self.temperature = OPENAI_TEMPERATURE
    
    def get_response(self, messages):
        """Send messages to OpenAI and get response"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

