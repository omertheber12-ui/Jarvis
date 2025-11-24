"""
Tests for src/openai_client.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.openai_client import OpenAIClient


class TestOpenAIClient:
    """Test OpenAIClient class"""
    
    @patch('src.openai_client.OPENAI_API_KEY', 'test-key-123')
    def test_initialization_with_key(self):
        """Test that client initializes with API key"""
        with patch('src.openai_client.OpenAI') as mock_openai:
            client = OpenAIClient()
            assert client.model is not None
            assert client.temperature is not None
            mock_openai.assert_called_once_with(api_key='test-key-123')
    
    @patch('src.openai_client.OPENAI_API_KEY', None)
    def test_initialization_without_key_raises_error(self):
        """Test that initialization fails without API key"""
        with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
            OpenAIClient()
    
    @patch('src.openai_client.OPENAI_API_KEY', 'test-key-123')
    def test_get_response_success(self):
        """Test successful API response"""
        with patch('src.openai_client.OpenAI') as mock_openai_class:
            # Mock the OpenAI client and response
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            
            # Mock the chat completion response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response from AI"
            mock_client.chat.completions.create.return_value = mock_response
            
            client = OpenAIClient()
            messages = [{"role": "user", "content": "Hello"}]
            response = client.get_response(messages)
            
            assert response == "Test response from AI"
            mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.openai_client.OPENAI_API_KEY', 'test-key-123')
    def test_get_response_api_error(self):
        """Test handling of API errors"""
        with patch('src.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            
            client = OpenAIClient()
            messages = [{"role": "user", "content": "Hello"}]
            
            with pytest.raises(Exception, match="OpenAI API error"):
                client.get_response(messages)

