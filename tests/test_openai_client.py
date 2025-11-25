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
    @patch('src.openai_client.api_logger')
    def test_get_response_success(self, mock_logger):
        """Test successful API response"""
        with patch('src.openai_client.OpenAI') as mock_openai_class:
            # Mock the OpenAI client and response
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            
            # Mock the chat completion response
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content = "Test response from AI"
            mock_message.role = "assistant"
            mock_message.tool_calls = []
            mock_choice.message = mock_message
            mock_choice.finish_reason = "stop"
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            
            client = OpenAIClient()
            messages = [{"role": "user", "content": "Hello"}]
            response = client.get_response(messages)
            
            assert response.content == "Test response from AI"
            assert response.tool_calls == []
            assert response.message["content"] == "Test response from AI"
            mock_client.chat.completions.create.assert_called_once()
            mock_logger.log_call.assert_called_once()
            log_kwargs = mock_logger.log_call.call_args.kwargs
            assert log_kwargs["service"] == "openai"
            assert log_kwargs.get("error") is None
            assert log_kwargs["response"]["choice_count"] == 1
    
    @patch('src.openai_client.OPENAI_API_KEY', 'test-key-123')
    @patch('src.openai_client.api_logger')
    def test_get_response_with_tool_call(self, mock_logger):
        """Test that tool calls are parsed correctly"""
        with patch('src.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_tool_function = MagicMock()
            mock_tool_function.name = "list_upcoming_events"
            mock_tool_function.arguments = '{"max_results": 3}'
            mock_tool_call = MagicMock()
            mock_tool_call.id = "tool_123"
            mock_tool_call.type = "function"
            mock_tool_call.function = mock_tool_function
            
            mock_message = MagicMock()
            mock_message.content = None
            mock_message.role = "assistant"
            mock_message.tool_calls = [mock_tool_call]
            
            mock_choice.message = mock_message
            mock_choice.finish_reason = "tool_calls"
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            
            client = OpenAIClient()
            response = client.get_response([{"role": "user", "content": "Hello"}])
            
            assert response.content is None
            assert len(response.tool_calls) == 1
            assert response.tool_calls[0].name == "list_upcoming_events"
            assert response.tool_calls[0].arguments == {"max_results": 3}
            mock_logger.log_call.assert_called_once()
    
    @patch('src.openai_client.OPENAI_API_KEY', 'test-key-123')
    @patch('src.openai_client.api_logger')
    def test_get_response_api_error(self, mock_logger):
        """Test handling of API errors"""
        with patch('src.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            
            client = OpenAIClient()
            messages = [{"role": "user", "content": "Hello"}]
            
            with pytest.raises(Exception, match="OpenAI API error"):
                client.get_response(messages)
            mock_logger.log_call.assert_called_once()
            log_kwargs = mock_logger.log_call.call_args.kwargs
            assert log_kwargs["service"] == "openai"
            assert "API Error" in log_kwargs["error"]

    @patch('src.openai_client.ENABLE_CALENDAR', False)
    @patch('src.openai_client.ENABLE_TASKS', False)
    def test_client_without_tools(self):
        """Client should omit tools when features disabled"""
        with patch('src.openai_client.OpenAI'):
            client = OpenAIClient()
            assert client.tools == []

