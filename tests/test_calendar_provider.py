"""
Tests for src/calendar/google_calendar_provider.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.calendar.google_calendar_provider import GoogleCalendarProvider, CalendarEvent
from src.config import GOOGLE_CREDENTIALS_FILE, GOOGLE_TOKEN_FILE


class TestCalendarEvent:
    """Test CalendarEvent dataclass"""
    
    def test_calendar_event_creation(self):
        """Test creating a CalendarEvent"""
        event = CalendarEvent(
            event_id="abc123",
            summary="Test Event",
            start="2024-01-01T10:00:00",
            end="2024-01-01T11:00:00",
            description="Demo",
            location="Room 1",
        )
        assert event.event_id == "abc123"
        assert event.summary == "Test Event"
        assert event.start == "2024-01-01T10:00:00"
        assert event.end == "2024-01-01T11:00:00"
        assert event.description == "Demo"


class TestGoogleCalendarProvider:
    """Test GoogleCalendarProvider class"""
    
    def test_initialization_defaults(self):
        """Test provider initialization with defaults"""
        provider = GoogleCalendarProvider()
        assert provider.credentials_path == Path(GOOGLE_CREDENTIALS_FILE)
        assert provider.token_path == Path(GOOGLE_TOKEN_FILE)
        assert len(provider.scopes) > 0
        assert provider.allow_interactive_auth is False
    
    def test_initialization_custom_paths(self):
        """Test provider initialization with custom paths"""
        provider = GoogleCalendarProvider(
            credentials_path="custom_creds.json",
            token_path="custom_token.json"
        )
        assert provider.credentials_path == Path("custom_creds.json")
        assert provider.token_path == Path("custom_token.json")
    
    @patch('src.calendar.google_calendar_provider.Credentials')
    @patch('pathlib.Path.exists')
    def test_ensure_authenticated_with_valid_token(self, mock_exists, mock_credentials_class):
        """Test authentication with existing valid token"""
        mock_exists.return_value = True
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials_class.from_authorized_user_file.return_value = mock_creds
        
        provider = GoogleCalendarProvider()
        creds = provider.ensure_authenticated()
        
        assert creds == mock_creds
        assert provider._creds == mock_creds
    
    @patch('src.calendar.google_calendar_provider.Credentials')
    @patch('pathlib.Path.exists')
    def test_ensure_authenticated_with_expired_token(self, mock_exists, mock_credentials_class):
        """Test authentication with expired token that can be refreshed"""
        mock_exists.return_value = True
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token_here"
        
        # After refresh, make creds valid
        def make_valid(*args):
            mock_creds.valid = True
            mock_creds.expired = False
        
        mock_creds.refresh.side_effect = make_valid
        mock_credentials_class.from_authorized_user_file.return_value = mock_creds
        
        with patch('src.calendar.google_calendar_provider.Request') as mock_request:
            provider = GoogleCalendarProvider()
            creds = provider.ensure_authenticated()
            
            mock_creds.refresh.assert_called_once()
            assert creds == mock_creds
    
    @patch('src.calendar.google_calendar_provider.api_logger')
    @patch('src.calendar.google_calendar_provider.build')
    @patch('src.calendar.google_calendar_provider.GoogleCalendarProvider.ensure_authenticated')
    def test_list_upcoming_events_success(self, mock_ensure_auth, mock_build, mock_logger):
        """Test successful listing of upcoming events"""
        # Mock credentials
        mock_creds = MagicMock()
        mock_ensure_auth.return_value = mock_creds
        
        # Mock service and API response
        mock_service = MagicMock()
        mock_events_list = MagicMock()
        mock_events_list.execute.return_value = {
            "items": [
                {
                    "summary": "Test Event 1",
                    "start": {"dateTime": "2024-01-01T10:00:00Z"},
                    "end": {"dateTime": "2024-01-01T11:00:00Z"}
                },
                {
                    "summary": "Test Event 2",
                    "start": {"date": "2024-01-02"},
                    "end": {"date": "2024-01-02"}
                }
            ]
        }
        mock_service.events.return_value.list.return_value = mock_events_list
        mock_build.return_value = mock_service
        
        provider = GoogleCalendarProvider()
        provider._service = mock_service  # Set service directly to skip build
        
        with patch('src.calendar.google_calendar_provider.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.isoformat.return_value = "2024-01-01T00:00:00Z"
            mock_datetime.now.return_value = mock_now
            
            events = provider.list_upcoming_events(max_results=5)
            
            assert len(events) == 2
            assert isinstance(events[0], CalendarEvent)
            assert events[0].summary == "Test Event 1"
            assert events[1].summary == "Test Event 2"
            mock_logger.log_call.assert_called_once()
            log_kwargs = mock_logger.log_call.call_args.kwargs
            assert log_kwargs["service"] == "google_calendar"
            assert log_kwargs.get("error") is None
            assert log_kwargs["response"]["returned_events"] == 2
    
    @patch('src.calendar.google_calendar_provider.api_logger')
    @patch('src.calendar.google_calendar_provider.build')
    @patch('src.calendar.google_calendar_provider.GoogleCalendarProvider.ensure_authenticated')
    def test_list_upcoming_events_empty(self, mock_ensure_auth, mock_build, mock_logger):
        """Test listing events when calendar is empty"""
        mock_creds = MagicMock()
        mock_ensure_auth.return_value = mock_creds
        
        mock_service = MagicMock()
        mock_events_list = MagicMock()
        mock_events_list.execute.return_value = {"items": []}
        mock_service.events.return_value.list.return_value = mock_events_list
        mock_build.return_value = mock_service
        
        provider = GoogleCalendarProvider()
        provider._service = mock_service
        
        with patch('src.calendar.google_calendar_provider.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.isoformat.return_value = "2024-01-01T00:00:00Z"
            mock_datetime.now.return_value = mock_now
            
            events = provider.list_upcoming_events()
            assert len(events) == 0
            mock_logger.log_call.assert_called_once()
            log_kwargs = mock_logger.log_call.call_args.kwargs
            assert log_kwargs["response"]["returned_events"] == 0
    
    @patch('src.calendar.google_calendar_provider.api_logger')
    @patch('src.calendar.google_calendar_provider.build')
    @patch('src.calendar.google_calendar_provider.GoogleCalendarProvider.ensure_authenticated')
    def test_list_upcoming_events_api_error(self, mock_ensure_auth, mock_build, mock_logger):
        """Test handling of API errors"""
        from googleapiclient.errors import HttpError
        
        mock_creds = MagicMock()
        mock_ensure_auth.return_value = mock_creds
        
        mock_service = MagicMock()
        mock_events_list = MagicMock()
        mock_error = HttpError(Mock(status=403), b'Forbidden')
        mock_events_list.execute.side_effect = mock_error
        mock_service.events.return_value.list.return_value = mock_events_list
        mock_build.return_value = mock_service
        
        provider = GoogleCalendarProvider()
        provider._service = mock_service
        
        with patch('src.calendar.google_calendar_provider.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.isoformat.return_value = "2024-01-01T00:00:00Z"
            mock_datetime.now.return_value = mock_now
            
            with pytest.raises(RuntimeError, match="Google Calendar API error"):
                provider.list_upcoming_events()
            mock_logger.log_call.assert_called_once()
            log_kwargs = mock_logger.log_call.call_args.kwargs
            assert "google_calendar" in log_kwargs["service"]
            assert log_kwargs["error"] is not None

    @patch('src.calendar.google_calendar_provider.api_logger')
    @patch('src.calendar.google_calendar_provider.build')
    @patch('src.calendar.google_calendar_provider.GoogleCalendarProvider.ensure_authenticated')
    def test_list_events_in_range(self, mock_ensure_auth, mock_build, mock_logger):
        """Test fetching events between start/end"""
        mock_creds = MagicMock()
        mock_ensure_auth.return_value = mock_creds

        mock_service = MagicMock()
        mock_events_list = MagicMock()
        mock_events_list.execute.return_value = {
            "items": [
                {
                    "id": "evt_1",
                    "summary": "Conflict",
                    "start": {"dateTime": "2024-01-01T10:00:00Z"},
                    "end": {"dateTime": "2024-01-01T11:00:00Z"},
                }
            ]
        }
        mock_service.events.return_value.list.return_value = mock_events_list
        mock_build.return_value = mock_service

        provider = GoogleCalendarProvider()
        provider._service = mock_service

        with patch('src.calendar.google_calendar_provider.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.isoformat.return_value = "2024-01-01T00:00:00Z"
            mock_datetime.now.return_value = mock_now

            events = provider.list_events_in_range(
                "2024-01-01T09:00:00Z", "2024-01-01T12:00:00Z"
            )
            assert len(events) == 1
            assert events[0].event_id == "evt_1"
            mock_logger.log_call.assert_called()

    @patch('src.calendar.google_calendar_provider.api_logger')
    @patch('src.calendar.google_calendar_provider.build')
    @patch('src.calendar.google_calendar_provider.GoogleCalendarProvider.ensure_authenticated')
    def test_create_event(self, mock_ensure_auth, mock_build, mock_logger):
        """Test creating a new event"""
        mock_creds = MagicMock()
        mock_ensure_auth.return_value = mock_creds
        mock_service = MagicMock()
        mock_insert = MagicMock()
        mock_insert.execute.return_value = {
            "id": "evt_2",
            "summary": "Planning",
            "start": {"dateTime": "2024-02-01T10:00:00Z"},
            "end": {"dateTime": "2024-02-01T11:00:00Z"},
        }
        mock_service.events.return_value.insert.return_value = mock_insert
        mock_build.return_value = mock_service

        provider = GoogleCalendarProvider()
        provider._service = mock_service

        event = provider.create_event(
            summary="Planning",
            start_time="2024-02-01T10:00:00Z",
            end_time="2024-02-01T11:00:00Z",
        )
        assert event.event_id == "evt_2"
        mock_logger.log_call.assert_called()

    @patch('src.calendar.google_calendar_provider.api_logger')
    @patch('src.calendar.google_calendar_provider.build')
    @patch('src.calendar.google_calendar_provider.GoogleCalendarProvider.ensure_authenticated')
    def test_update_event_requires_fields(self, mock_ensure_auth, mock_build, mock_logger):
        """Test updating without fields raises error"""
        provider = GoogleCalendarProvider()
        with pytest.raises(ValueError):
            provider.update_event("evt_missing")
        mock_logger.assert_not_called()

    @patch('src.calendar.google_calendar_provider.api_logger')
    @patch('src.calendar.google_calendar_provider.build')
    @patch('src.calendar.google_calendar_provider.GoogleCalendarProvider.ensure_authenticated')
    def test_delete_event(self, mock_ensure_auth, mock_build, mock_logger):
        """Test deleting event"""
        mock_service = MagicMock()
        mock_service.events.return_value.delete.return_value.execute.return_value = None
        mock_build.return_value = mock_service

        provider = GoogleCalendarProvider()
        provider._service = mock_service
        provider.delete_event("evt_3")
        mock_logger.log_call.assert_called()

