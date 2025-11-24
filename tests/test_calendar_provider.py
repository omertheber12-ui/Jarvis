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
            summary="Test Event",
            start="2024-01-01T10:00:00",
            end="2024-01-01T11:00:00"
        )
        assert event.summary == "Test Event"
        assert event.start == "2024-01-01T10:00:00"
        assert event.end == "2024-01-01T11:00:00"


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
    
    @patch('src.calendar.google_calendar_provider.build')
    @patch('src.calendar.google_calendar_provider.GoogleCalendarProvider.ensure_authenticated')
    def test_list_upcoming_events_success(self, mock_ensure_auth, mock_build):
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
    
    @patch('src.calendar.google_calendar_provider.build')
    @patch('src.calendar.google_calendar_provider.GoogleCalendarProvider.ensure_authenticated')
    def test_list_upcoming_events_empty(self, mock_ensure_auth, mock_build):
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
    
    @patch('src.calendar.google_calendar_provider.build')
    @patch('src.calendar.google_calendar_provider.GoogleCalendarProvider.ensure_authenticated')
    def test_list_upcoming_events_api_error(self, mock_ensure_auth, mock_build):
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

