"""
OpenAI API client - handles communication with OpenAI API
"""

import os
from openai import OpenAI
from .config import OPENAI_MODEL, OPENAI_TEMPERATURE


class OpenAIClient:
    """Handles communication with OpenAI API"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key)
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

