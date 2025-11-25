"""
Google Calendar provider
------------------------

Wraps OAuth credential loading, token refresh and convenient helper
methods for accessing the Calendar API. Initially only implements a
`list_upcoming_events` sanity check used while developing Feature 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..api_logger import api_logger
from ..config import GOOGLE_CREDENTIALS_FILE, GOOGLE_TOKEN_FILE

SCOPES = ["https://www.googleapis.com/auth/calendar"]
DEFAULT_CREDENTIALS_PATH = GOOGLE_CREDENTIALS_FILE
DEFAULT_TOKEN_PATH = GOOGLE_TOKEN_FILE
DEFAULT_CALENDAR_ID = "primary"


@dataclass
class CalendarEvent:
    """Lightweight representation of a Calendar event."""

    event_id: Optional[str]
    summary: str
    start: str
    end: str
    description: Optional[str] = None
    location: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "id": self.event_id,
            "summary": self.summary,
            "start": self.start,
            "end": self.end,
            "description": self.description,
            "location": self.location,
        }


class GoogleCalendarProvider:
    """
    Handles Google Calendar OAuth credentials and API calls.

    Parameters
    ----------
    credentials_path: Path-like
        Location of OAuth client credentials downloaded from Google Cloud.
    token_path: Path-like
        Where to persist the user access/refresh tokens.
    scopes: list[str]
        OAuth scopes (defaults to read-only access while we prototype).     
    allow_interactive_auth: bool
        Whether the provider may launch a browser flow when tokens are
        missing/invalid. Jarvis runtime should keep this False to avoid     
        blocking. The standalone authentication helper enables it.
    """

    def __init__(
        self,
        credentials_path: Path | str | None = None,
        token_path: Path | str | None = None,
        scopes: Optional[List[str]] = None,
        allow_interactive_auth: bool = False,
    ):
        self.credentials_path = Path(credentials_path or DEFAULT_CREDENTIALS_PATH)
        self.token_path = Path(token_path or DEFAULT_TOKEN_PATH)
        self.scopes = scopes or SCOPES
        self.allow_interactive_auth = allow_interactive_auth
        self._creds: Optional[Credentials] = None
        self._service = None

    # ------------------------------------------------------------------
    # Credential helpers
    # ------------------------------------------------------------------
    def ensure_authenticated(self) -> Credentials:
        """
        Load or refresh credentials and return a valid Credentials object.

        Raises RuntimeError if credentials cannot be obtained without
        interactive flow and `allow_interactive_auth` is False.
        """
        if self._creds and self._creds.valid:
            return self._creds

        creds = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(
                str(self.token_path), scopes=self.scopes
            )

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif (not creds or not creds.valid) and self.allow_interactive_auth:
            self._assert_credentials_file()
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_path), self.scopes
            )
            creds = flow.run_local_server(port=0)
            self._save_credentials(creds)

        if not creds or not creds.valid:
            raise RuntimeError(
                "Google Calendar token missing or invalid. "
                "Run `python scripts/authenticate_calendar.py` to authorize access."
            )

        self._creds = creds
        return creds

    def _assert_credentials_file(self) -> None:
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Client credentials not found at {self.credentials_path}. "
                "Download them from Google Cloud Console."
            )

    def _save_credentials(self, creds: Credentials) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(creds.to_json(), encoding="utf-8")
    
    def _normalize_event(self, event_data: dict) -> CalendarEvent:
        start = event_data.get("start", {}).get("dateTime") or event_data.get(
            "start", {}
        ).get("date")
        end = event_data.get("end", {}).get("dateTime") or event_data.get("end", {}).get(
            "date"
        )
        return CalendarEvent(
            event_id=event_data.get("id"),
            summary=event_data.get("summary", "(no title)"),
            start=start or "",
            end=end or "",
            description=event_data.get("description"),
            location=event_data.get("location"),
        )

    def _build_time_block(self, value: str) -> Dict[str, str]:
        value = (value or "").strip()
        if not value:
            raise ValueError("Calendar time values cannot be empty.")
        if "T" in value:
            return {"dateTime": value}
        return {"date": value}

    # ------------------------------------------------------------------
    # Service helpers
    # ------------------------------------------------------------------
    def _get_service(self):
        if self._service is None:
            creds = self.ensure_authenticated()
            self._service = build("calendar", "v3", credentials=creds)
        return self._service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def list_upcoming_events(self, max_results: int = 5) -> List[CalendarEvent]:
        """
        Fetch upcoming events from the primary calendar.

        Returns a list of CalendarEvent dataclasses sorted chronologically. 
        """
        service = self._get_service()
        now = datetime.now(timezone.utc).isoformat()

        request_summary = {
            "calendar_id": "primary",
            "max_results": max_results,
            "time_min": now,
        }
        timer_start = perf_counter()

        try:
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
        except HttpError as exc:
            api_logger.log_call(
                service="google_calendar",
                action="events.list",
                request=request_summary,
                error=str(exc),
                metadata={"duration_ms": int((perf_counter() - timer_start) * 1000)},
            )
            raise RuntimeError(f"Google Calendar API error: {exc}") from exc

        events = [self._normalize_event(event) for event in events_result.get("items", [])]
        api_logger.log_call(
            service="google_calendar",
            action="events.list",
            request=request_summary,
            response={
                "returned_events": len(events),
                "context": "upcoming_events",
            },
            metadata={"duration_ms": int((perf_counter() - timer_start) * 1000)},
        )
        return events

    def list_events_in_range(
        self, start_time: str, end_time: str, max_results: int = 25
    ) -> List[CalendarEvent]:
        service = self._get_service()
        request_summary = {
            "calendar_id": DEFAULT_CALENDAR_ID,
            "time_min": start_time,
            "time_max": end_time,
            "max_results": max_results,
        }
        timer_start = perf_counter()

        try:
            events_result = (
                service.events()
                .list(
                    calendarId=DEFAULT_CALENDAR_ID,
                    timeMin=start_time,
                    timeMax=end_time,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
        except HttpError as exc:
            api_logger.log_call(
                service="google_calendar",
                action="events.list",
                request=request_summary,
                error=str(exc),
                metadata={"duration_ms": int((perf_counter() - timer_start) * 1000)},
            )
            raise RuntimeError(f"Google Calendar API error: {exc}") from exc

        events = [self._normalize_event(event) for event in events_result.get("items", [])]
        api_logger.log_call(
            service="google_calendar",
            action="events.list",
            request=request_summary,
            response={
                "returned_events": len(events),
                "context": "availability_check",
            },
            metadata={"duration_ms": int((perf_counter() - timer_start) * 1000)},
        )
        return events

    def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> CalendarEvent:
        service = self._get_service()
        event_body = {
            "summary": summary,
            "start": self._build_time_block(start_time),
            "end": self._build_time_block(end_time),
        }
        if description:
            event_body["description"] = description
        if location:
            event_body["location"] = location

        timer_start = perf_counter()
        try:
            created = (
                service.events()
                .insert(calendarId=DEFAULT_CALENDAR_ID, body=event_body)
                .execute()
            )
        except HttpError as exc:
            api_logger.log_call(
                service="google_calendar",
                action="events.insert",
                request={"summary": summary},
                error=str(exc),
                metadata={"duration_ms": int((perf_counter() - timer_start) * 1000)},
            )
            raise RuntimeError(f"Google Calendar API error: {exc}") from exc

        api_logger.log_call(
            service="google_calendar",
            action="events.insert",
            request={"summary": summary},
            response={"event_id": created.get("id")},
            metadata={"duration_ms": int((perf_counter() - timer_start) * 1000)},
        )
        return self._normalize_event(created)

    def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> CalendarEvent:
        service = self._get_service()
        body: Dict[str, Dict[str, str] | str] = {}
        if summary:
            body["summary"] = summary
        if start_time:
            body["start"] = self._build_time_block(start_time)
        if end_time:
            body["end"] = self._build_time_block(end_time)
        if description is not None:
            body["description"] = description
        if location is not None:
            body["location"] = location
        if not body:
            raise ValueError("No update fields provided for calendar event.")

        timer_start = perf_counter()
        try:
            updated = (
                service.events()
                .patch(
                    calendarId=DEFAULT_CALENDAR_ID,
                    eventId=event_id,
                    body=body,
                )
                .execute()
            )
        except HttpError as exc:
            api_logger.log_call(
                service="google_calendar",
                action="events.patch",
                request={"event_id": event_id},
                error=str(exc),
                metadata={"duration_ms": int((perf_counter() - timer_start) * 1000)},
            )
            raise RuntimeError(f"Google Calendar API error: {exc}") from exc

        api_logger.log_call(
            service="google_calendar",
            action="events.patch",
            request={"event_id": event_id},
            response={"status": "updated"},
            metadata={"duration_ms": int((perf_counter() - timer_start) * 1000)},
        )
        return self._normalize_event(updated)

    def delete_event(self, event_id: str) -> None:
        service = self._get_service()
        timer_start = perf_counter()
        try:
            service.events().delete(
                calendarId=DEFAULT_CALENDAR_ID, eventId=event_id
            ).execute()
        except HttpError as exc:
            api_logger.log_call(
                service="google_calendar",
                action="events.delete",
                request={"event_id": event_id},
                error=str(exc),
                metadata={"duration_ms": int((perf_counter() - timer_start) * 1000)},
            )
            raise RuntimeError(f"Google Calendar API error: {exc}") from exc

        api_logger.log_call(
            service="google_calendar",
            action="events.delete",
            request={"event_id": event_id},
            response={"status": "deleted"},
            metadata={"duration_ms": int((perf_counter() - timer_start) * 1000)},
        )
