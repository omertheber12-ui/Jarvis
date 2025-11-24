"""
Tests for src/conversation_manager.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.conversation_manager import ConversationManager
from src.config import MAX_MESSAGE_LENGTH


class TestConversationManager:
    """Test ConversationManager class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('src.conversation_manager.OpenAIClient'):
            self.manager = ConversationManager()
    
    def test_initialization(self):
        """Test that manager initializes correctly"""
        assert self.manager.storage is not None
        assert self.manager.api_client is not None
    
    def test_validate_message_empty(self):
        """Test validation of empty message"""
        is_valid, error = self.manager.validate_message("")
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_validate_message_whitespace_only(self):
        """Test validation of whitespace-only message"""
        is_valid, error = self.manager.validate_message("   \n\t  ")
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_validate_message_valid(self):
        """Test validation of valid message"""
        is_valid, error = self.manager.validate_message("Hello, Jarvis!")
        assert is_valid is True
        assert error is None
    
    def test_validate_message_too_long(self):
        """Test validation of message exceeding length limit"""
        long_message = "x" * (MAX_MESSAGE_LENGTH + 1)
        is_valid, error = self.manager.validate_message(long_message)
        assert is_valid is False
        assert str(MAX_MESSAGE_LENGTH) in error
    
    def test_validate_message_at_limit(self):
        """Test validation of message at exact limit"""
        message = "x" * MAX_MESSAGE_LENGTH
        is_valid, error = self.manager.validate_message(message)
        assert is_valid is True
        assert error is None
    
    @patch('src.conversation_manager.ConversationStorage')
    @patch('src.conversation_manager.OpenAIClient')
    def test_process_message_success(self, mock_openai_class, mock_storage_class):
        """Test successful message processing"""
        # Setup mocks
        mock_storage = Mock()
        mock_storage.get_or_create_session.return_value = {
            "messages": [{"role": "system", "content": "You are Jarvis"}]
        }
        mock_storage_class.return_value = mock_storage
        
        mock_client = Mock()
        mock_client.get_response.return_value = "Hello! How can I help?"
        mock_openai_class.return_value = mock_client
        
        manager = ConversationManager()
        response, error = manager.process_message("session1", "Hello")
        
        assert error is None
        assert response == "Hello! How can I help?"
        mock_storage.add_message.assert_called()
    
    @patch('src.conversation_manager.ConversationStorage')
    @patch('src.conversation_manager.OpenAIClient')
    def test_process_message_validation_failure(self, mock_openai_class, mock_storage_class):
        """Test message processing with validation failure"""
        manager = ConversationManager()
        response, error = manager.process_message("session1", "")
        
        assert response is None
        assert error is not None
        assert "empty" in error.lower()
    
    @patch('src.conversation_manager.ConversationStorage')
    @patch('src.conversation_manager.OpenAIClient')
    def test_process_message_api_error(self, mock_openai_class, mock_storage_class):
        """Test message processing with API error"""
        mock_storage = Mock()
        mock_storage.get_or_create_session.return_value = {
            "messages": [{"role": "system", "content": "You are Jarvis"}]
        }
        mock_storage_class.return_value = mock_storage
        
        mock_client = Mock()
        mock_client.get_response.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        manager = ConversationManager()
        response, error = manager.process_message("session1", "Hello")
        
        assert response is None
        assert error is not None
        assert "API Error" in error

