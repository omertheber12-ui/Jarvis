"""
Tests for Flask routes in jarvis_chat.py
"""

import pytest
from unittest.mock import patch, MagicMock
from jarvis_chat import app


class TestFlaskRoutes:
    """Test Flask application routes"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_index_route(self, client):
        """Test index route returns HTML"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'html' in response.data.lower() or b'<!DOCTYPE' in response.data
    
    def test_chat_route_missing_json(self, client):
        """Test chat route with non-JSON request"""
        response = client.post('/chat', data="not json")
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "JSON" in data["error"]
    
    def test_chat_route_empty_message(self, client):
        """Test chat route with empty message"""
        response = client.post('/chat', 
                             json={"message": "", "session_id": "test"})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "empty" in data["error"].lower()
    
    def test_chat_route_missing_message(self, client):
        """Test chat route with missing message field"""
        response = client.post('/chat', json={"session_id": "test"})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
    
    @patch('jarvis_chat.get_conv_manager')
    def test_chat_route_success(self, mock_get_manager, client):
        """Test successful chat request"""
        # Mock conversation manager
        mock_manager = MagicMock()
        mock_manager.process_message.return_value = ("Hello! How can I help?", None)
        mock_get_manager.return_value = mock_manager
        
        response = client.post('/chat',
                             json={"message": "Hello", "session_id": "test123"})
        assert response.status_code == 200
        data = response.get_json()
        assert "response" in data
        assert data["response"] == "Hello! How can I help?"
        assert data["session_id"] == "test123"
    
    @patch('jarvis_chat.get_conv_manager')
    def test_chat_route_processing_error(self, mock_get_manager, client):
        """Test chat route with processing error"""
        mock_manager = MagicMock()
        mock_manager.process_message.return_value = (None, "Processing error")
        mock_get_manager.return_value = mock_manager
        
        response = client.post('/chat',
                             json={"message": "Hello", "session_id": "test123"})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "Processing error" in data["error"]
    
    @patch('jarvis_chat.ConversationStorage')
    def test_history_route(self, mock_storage_class, client):
        """Test history route"""
        mock_storage = MagicMock()
        mock_storage.get_or_create_session.return_value = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        }
        mock_storage_class.return_value = mock_storage
        
        response = client.get('/history/test_session')
        assert response.status_code == 200
        data = response.get_json()
        assert "messages" in data
        assert len(data["messages"]) == 2
        # System messages should be filtered out
        assert all(msg["role"] != "system" for msg in data["messages"])

