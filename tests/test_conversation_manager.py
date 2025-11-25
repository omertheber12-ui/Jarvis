"""
Tests for src/conversation_manager.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.conversation_manager import ConversationManager
from src.config import MAX_MESSAGE_LENGTH
from src.openai_client import ModelResponse, ToolRequest


class TestConversationManager:
    """Test ConversationManager class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('src.conversation_manager.OpenAIClient'), patch(
            'src.conversation_manager.GoogleCalendarProvider'
        ), patch('src.conversation_manager.TaskManager'):
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
    
    @patch('src.conversation_manager.TaskManager')
    @patch('src.conversation_manager.GoogleCalendarProvider')
    @patch('src.conversation_manager.ConversationStorage')
    @patch('src.conversation_manager.OpenAIClient')
    def test_process_message_success(
        self, mock_openai_class, mock_storage_class, mock_calendar_class, mock_task_manager
    ):
        """Test successful message processing"""
        # Setup mocks
        mock_storage = Mock()
        mock_storage.get_or_create_session.return_value = {
            "messages": [{"role": "system", "content": "You are Jarvis"}]
        }
        mock_storage_class.return_value = mock_storage
        
        mock_client = Mock()
        mock_client.get_response.return_value = ModelResponse(
            content="Hello! How can I help?",
            tool_calls=[],
            message={"role": "assistant", "content": "Hello! How can I help?"},
            finish_reason="stop",
        )
        mock_openai_class.return_value = mock_client
        mock_calendar_class.return_value = Mock()
        mock_task_manager.return_value = Mock()
        
        manager = ConversationManager()
        response, error = manager.process_message("session1", "Hello")
        
        assert error is None
        assert response == "Hello! How can I help?"
        mock_storage.add_message.assert_called()
    
    @patch('src.conversation_manager.TaskManager')
    @patch('src.conversation_manager.GoogleCalendarProvider')
    @patch('src.conversation_manager.ConversationStorage')
    @patch('src.conversation_manager.OpenAIClient')
    def test_process_message_validation_failure(
        self, mock_openai_class, mock_storage_class, mock_calendar_class, mock_task_manager
    ):
        """Test message processing with validation failure"""
        manager = ConversationManager()
        response, error = manager.process_message("session1", "")
        
        assert response is None
        assert error is not None
        assert "empty" in error.lower()
    
    @patch('src.conversation_manager.TaskManager')
    @patch('src.conversation_manager.GoogleCalendarProvider')
    @patch('src.conversation_manager.ConversationStorage')
    @patch('src.conversation_manager.OpenAIClient')
    def test_process_message_api_error(
        self, mock_openai_class, mock_storage_class, mock_calendar_class, mock_task_manager
    ):
        """Test message processing with API error"""
        mock_storage = Mock()
        mock_storage.get_or_create_session.return_value = {
            "messages": [{"role": "system", "content": "You are Jarvis"}]
        }
        mock_storage_class.return_value = mock_storage
        
        mock_client = Mock()
        mock_client.get_response.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        mock_calendar_class.return_value = Mock()
        mock_task_manager.return_value = Mock()
        
        manager = ConversationManager()
        response, error = manager.process_message("session1", "Hello")
        
        assert response is None
        assert error is not None
        assert "API Error" in error
    
    @patch('src.conversation_manager.TaskManager')
    @patch('src.conversation_manager.GoogleCalendarProvider')
    @patch('src.conversation_manager.ConversationStorage')
    @patch('src.conversation_manager.OpenAIClient')
    def test_process_message_with_tool_call(
        self, mock_openai_class, mock_storage_class, mock_calendar_class, mock_task_manager
    ):
        """Test processing when model requests a calendar tool"""
        mock_storage = Mock()
        mock_storage.get_or_create_session.return_value = {
            "messages": [{"role": "system", "content": "You are Jarvis"}]
        }
        mock_storage_class.return_value = mock_storage

        mock_calendar = Mock()
        mock_calendar.list_events_in_range.return_value = []
        fake_event = Mock()
        fake_event.to_dict.return_value = {"id": "evt_10", "summary": "Meeting"}
        mock_calendar.create_event.return_value = fake_event
        mock_calendar_class.return_value = mock_calendar
        mock_task_manager.return_value = Mock()

        tool_request = ToolRequest(
            id="tool_1",
            name="create_calendar_event",
            arguments={
                "summary": "Meeting",
                "start_time": "2024-03-01T10:00:00Z",
                "end_time": "2024-03-01T11:00:00Z",
            },
        )
        assistant_tool_message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "tool_1",
                    "type": "function",
                    "function": {
                        "name": "create_calendar_event",
                        "arguments": '{"summary": "Meeting"}',
                    },
                }
            ],
        }
        first_response = ModelResponse(
            content=None,
            tool_calls=[tool_request],
            message=assistant_tool_message,
            finish_reason="tool_calls",
        )
        second_response = ModelResponse(
            content="Event created!",
            tool_calls=[],
            message={"role": "assistant", "content": "Event created!"},
            finish_reason="stop",
        )

        mock_client = Mock()
        mock_client.get_response.side_effect = [first_response, second_response]
        mock_openai_class.return_value = mock_client

        manager = ConversationManager()
        response, error = manager.process_message("session1", "Schedule a meeting")

        assert error is None
        assert response == "Event created!"
        mock_calendar.create_event.assert_called_once()

    @patch('src.conversation_manager.TaskManager')
    @patch('src.conversation_manager.GoogleCalendarProvider')
    @patch('src.conversation_manager.ConversationStorage')
    @patch('src.conversation_manager.OpenAIClient')
    def test_process_message_with_task_tool_call(
        self, mock_openai_class, mock_storage_class, mock_calendar_class, mock_task_manager
    ):
        """Test task creation via tool call"""
        mock_storage = Mock()
        mock_storage.get_or_create_session.return_value = {
            "messages": [{"role": "system", "content": "You are Jarvis"}]
        }
        mock_storage_class.return_value = mock_storage

        mock_calendar_class.return_value = Mock()
        mock_task = {"id": "task_1", "title": "Pay bills", "status": "pending"}
        mock_task_manager.return_value.create_task.return_value = mock_task

        tool_request = ToolRequest(
            id="tool_task",
            name="create_task",
            arguments={"title": "Pay bills"},
        )
        assistant_tool_message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "tool_task",
                    "type": "function",
                    "function": {
                        "name": "create_task",
                        "arguments": '{"title": "Pay bills"}',
                    },
                }
            ],
        }
        first_response = ModelResponse(
            content=None,
            tool_calls=[tool_request],
            message=assistant_tool_message,
            finish_reason="tool_calls",
        )
        final_response = ModelResponse(
            content="Task added!",
            tool_calls=[],
            message={"role": "assistant", "content": "Task added!"},
            finish_reason="stop",
        )

        mock_client = Mock()
        mock_client.get_response.side_effect = [first_response, final_response]
        mock_openai_class.return_value = mock_client

        manager = ConversationManager()
        response, error = manager.process_message("session1", "Remind me to pay bills")

        assert error is None
        assert response == "Task added!"
        mock_task_manager.return_value.create_task.assert_called_once_with(
            title="Pay bills",
            description=None,
            due_date=None,
            priority="normal",
        )

    @patch('src.conversation_manager.ENABLE_CALENDAR', False)
    @patch('src.conversation_manager.TaskManager')
    @patch('src.conversation_manager.GoogleCalendarProvider')
    @patch('src.conversation_manager.ConversationStorage')
    @patch('src.conversation_manager.OpenAIClient')
    def test_calendar_tools_disabled_message(
        self,
        mock_openai_class,
        mock_storage_class,
        mock_calendar_class,
        mock_task_manager,
    ):
        mock_storage = Mock()
        mock_storage.get_or_create_session.return_value = {"messages": []}
        mock_storage_class.return_value = mock_storage
        mock_openai_class.return_value = Mock()
        mock_calendar_class.return_value = Mock()
        mock_task_manager.return_value = Mock()

        manager = ConversationManager()
        tool_request = ToolRequest(id="t1", name="list_upcoming_events", arguments={})
        result = manager._execute_tool(tool_request)
        assert result["success"] is False
        assert "disabled" in result["error"].lower()

    @patch('src.conversation_manager.ENABLE_TASKS', False)
    @patch('src.conversation_manager.TaskManager')
    @patch('src.conversation_manager.GoogleCalendarProvider')
    @patch('src.conversation_manager.ConversationStorage')
    @patch('src.conversation_manager.OpenAIClient')
    def test_task_tools_disabled_message(
        self,
        mock_openai_class,
        mock_storage_class,
        mock_calendar_class,
        mock_task_manager,
    ):
        mock_storage = Mock()
        mock_storage.get_or_create_session.return_value = {"messages": []}
        mock_storage_class.return_value = mock_storage
        mock_openai_class.return_value = Mock()
        mock_calendar_class.return_value = Mock()
        mock_task_manager.return_value = Mock()

        manager = ConversationManager()
        tool_request = ToolRequest(id="t2", name="create_task", arguments={"title": "Test"})
        result = manager._execute_tool(tool_request)
        assert result["success"] is False
        assert "disabled" in result["error"].lower()

    @patch('src.conversation_manager.TaskManager')
    @patch('src.conversation_manager.GoogleCalendarProvider')
    @patch('src.conversation_manager.ConversationStorage')
    @patch('src.conversation_manager.OpenAIClient')
    def test_tool_configuration_guard_missing_handlers(
        self,
        mock_openai_class,
        mock_storage_class,
        mock_calendar_class,
        mock_task_manager,
    ):
        mock_openai_class.return_value = Mock()
        mock_storage_class.return_value = Mock()
        mock_calendar_class.return_value = Mock()
        mock_task_manager.return_value = Mock()

        def noop_register(self):
            # Intentionally skip registering handlers for configured tools
            return None

        with patch('src.conversation_manager.ENABLE_CALENDAR', True), patch(
            'src.conversation_manager.ENABLE_TASKS', True
        ), patch.object(
            ConversationManager, '_register_tool_handlers', noop_register
        ):
            with pytest.raises(RuntimeError, match="Missing handlers"):
                ConversationManager()

    @patch('src.conversation_manager.TaskManager')
    @patch('src.conversation_manager.GoogleCalendarProvider')
    @patch('src.conversation_manager.ConversationStorage')
    @patch('src.conversation_manager.OpenAIClient')
    def test_tool_configuration_guard_unexpected_handler(
        self,
        mock_openai_class,
        mock_storage_class,
        mock_calendar_class,
        mock_task_manager,
    ):
        mock_openai_class.return_value = Mock()
        mock_storage_class.return_value = Mock()
        mock_calendar_class.return_value = Mock()
        mock_task_manager.return_value = Mock()

        def rogue_register(self):
            self.tool_handlers['rogue_tool'] = lambda _: None

        with patch('src.conversation_manager.ENABLE_CALENDAR', False), patch(
            'src.conversation_manager.ENABLE_TASKS', False
        ), patch.object(
            ConversationManager, '_register_tool_handlers', rogue_register
        ):
            with pytest.raises(RuntimeError, match="Handlers registered without tool metadata"):
                ConversationManager()

