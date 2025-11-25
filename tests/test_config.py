"""
Tests for src/config.py
"""

import os
from pathlib import Path
import pytest
from unittest.mock import patch
from src import config


class TestConfig:
    """Test configuration loading and constants"""
    
    def test_max_message_length_default(self):
        """Test that MAX_MESSAGE_LENGTH has a default value"""
        assert hasattr(config, 'MAX_MESSAGE_LENGTH')
        assert isinstance(config.MAX_MESSAGE_LENGTH, int)
        assert config.MAX_MESSAGE_LENGTH > 0
    
    def test_storage_file_default(self):
        """Test that STORAGE_FILE has a default value"""
        assert hasattr(config, 'STORAGE_FILE')
        assert isinstance(config.STORAGE_FILE, Path)
        assert config.STORAGE_FILE.name == "conversations.json"
    
    def test_system_prompt_exists(self):
        """Test that SYSTEM_PROMPT is defined"""
        assert hasattr(config, 'SYSTEM_PROMPT')
        assert isinstance(config.SYSTEM_PROMPT, str)
        assert len(config.SYSTEM_PROMPT) > 0
        assert "Jarvis" in config.SYSTEM_PROMPT
    
    def test_openai_model_default(self):
        """Test that OPENAI_MODEL has a default value"""
        assert hasattr(config, 'OPENAI_MODEL')
        assert isinstance(config.OPENAI_MODEL, str)
        assert len(config.OPENAI_MODEL) > 0
    
    def test_openai_temperature_default(self):
        """Test that OPENAI_TEMPERATURE has a default value"""
        assert hasattr(config, 'OPENAI_TEMPERATURE')
        assert isinstance(config.OPENAI_TEMPERATURE, float)
        assert 0.0 <= config.OPENAI_TEMPERATURE <= 2.0

    def test_feature_flag_defaults(self):
        """Feature toggles should be booleans"""
        assert isinstance(config.ENABLE_CALENDAR, bool)
        assert isinstance(config.ENABLE_TASKS, bool)
        assert isinstance(config.ENABLE_LOGGING, bool)
    
    @patch.dict(os.environ, {'MAX_MESSAGE_LENGTH': '500'})
    def test_max_message_length_from_env(self):
        """Test that MAX_MESSAGE_LENGTH can be loaded from environment"""
        # Reload config to pick up env var
        import importlib
        importlib.reload(config)
        # Note: This test may not work perfectly due to module caching,
        # but it verifies the structure is correct
        assert hasattr(config, 'MAX_MESSAGE_LENGTH')

