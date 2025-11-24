"""
Tests for src/storage.py
"""

import json
import tempfile
import os
from pathlib import Path
from src.storage import ConversationStorage
from src.config import SYSTEM_PROMPT


class TestConversationStorage:
    """Test ConversationStorage class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.storage = ConversationStorage(storage_file=self.temp_file.name)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_storage_initialization(self):
        """Test that storage initializes correctly"""
        assert self.storage.storage_file == self.temp_file.name
        assert Path(self.temp_file.name).exists()
    
    def test_ensure_storage_file_creates_file(self):
        """Test that ensure_storage_file creates file if missing"""
        # Delete the file
        os.unlink(self.temp_file.name)
        # Reinitialize storage
        storage = ConversationStorage(storage_file=self.temp_file.name)
        assert Path(self.temp_file.name).exists()
    
    def test_load_conversations_empty(self):
        """Test loading empty conversations"""
        data = self.storage.load_conversations()
        assert isinstance(data, dict)
        assert "conversations" in data
        assert isinstance(data["conversations"], list)
    
    def test_save_and_load_conversations(self):
        """Test saving and loading conversations"""
        test_data = {
            "conversations": [
                {
                    "session_id": "test123",
                    "messages": [{"role": "system", "content": "test"}]
                }
            ]
        }
        self.storage.save_conversations(test_data)
        loaded = self.storage.load_conversations()
        assert loaded["conversations"][0]["session_id"] == "test123"
    
    def test_get_or_create_session_new(self):
        """Test creating a new session"""
        session = self.storage.get_or_create_session("new_session")
        assert session["session_id"] == "new_session"
        assert len(session["messages"]) == 1
        assert session["messages"][0]["role"] == "system"
        assert session["messages"][0]["content"] == SYSTEM_PROMPT
        assert "created_at" in session
    
    def test_get_or_create_session_existing(self):
        """Test retrieving an existing session"""
        # Create a session and add a message using the proper method
        self.storage.get_or_create_session("existing")
        self.storage.add_message("existing", "user", "test message")
        
        # Retrieve it
        session2 = self.storage.get_or_create_session("existing")
        assert session2["session_id"] == "existing"
        assert len(session2["messages"]) >= 2
        # Should have system message and user message
        assert any(msg["role"] == "user" and msg["content"] == "test message" 
                  for msg in session2["messages"])
    
    def test_add_message_to_existing_session(self):
        """Test adding message to existing session"""
        session_id = "test_session"
        self.storage.get_or_create_session(session_id)
        self.storage.add_message(session_id, "user", "Hello")
        
        session = self.storage.get_or_create_session(session_id)
        assert len(session["messages"]) == 2  # system + user
        assert session["messages"][-1]["role"] == "user"
        assert session["messages"][-1]["content"] == "Hello"
    
    def test_add_message_creates_session_if_missing(self):
        """Test that add_message creates session if it doesn't exist"""
        session_id = "new_session_from_message"
        self.storage.add_message(session_id, "user", "First message")
        
        session = self.storage.get_or_create_session(session_id)
        assert len(session["messages"]) == 2  # system + user
        assert session["messages"][-1]["content"] == "First message"

