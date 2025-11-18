"""
Conversation manager - orchestrates conversation flow and validation
"""

from .storage import ConversationStorage
from .openai_client import OpenAIClient
from .config import MAX_MESSAGE_LENGTH


class ConversationManager:
    """Manages conversation flow and validation"""
    
    def __init__(self):
        self.storage = ConversationStorage()
        self.api_client = OpenAIClient()
    
    def validate_message(self, message):
        """Validate message length"""
        if not message or not message.strip():
            return False, "Message cannot be empty"
        if len(message) > MAX_MESSAGE_LENGTH:
            return False, f"Message exceeds {MAX_MESSAGE_LENGTH} character limit"
        return True, None
    
    def process_message(self, session_id, user_message):
        """Process user message and get Jarvis response"""
        # Validate message
        is_valid, error = self.validate_message(user_message)
        if not is_valid:
            return None, error
        
        # Get conversation history
        session = self.storage.get_or_create_session(session_id)
        messages = session["messages"].copy()
        
        # Add user message
        messages.append({"role": "user", "content": user_message})
        self.storage.add_message(session_id, "user", user_message)
        
        # Get response from OpenAI
        try:
            jarvis_response = self.api_client.get_response(messages)
            
            # Save Jarvis response
            self.storage.add_message(session_id, "assistant", jarvis_response)
            
            return jarvis_response, None
        except Exception as e:
            return None, str(e)

