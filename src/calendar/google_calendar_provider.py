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
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config import GOOGLE_CREDENTIALS_FILE, GOOGLE_TOKEN_FILE

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
DEFAULT_CREDENTIALS_PATH = GOOGLE_CREDENTIALS_FILE
DEFAULT_TOKEN_PATH = GOOGLE_TOKEN_FILE


@dataclass
class CalendarEvent:
    """Lightweight representation of a Calendar event."""

    summary: str
    start: str
    end: str


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
            raise RuntimeError(f"Google Calendar API error: {exc}") from exc

        events = []
        for event in events_result.get("items", []):
            start = event.get("start", {}).get("dateTime") or event.get("start", {}).get(
                "date"
            )
            end = event.get("end", {}).get("dateTime") or event.get("end", {}).get(
                "date"
            )
            events.append(
                CalendarEvent(
                    summary=event.get("summary", "(no title)"),
                    start=start or "",
                    end=end or "",
                )
            )
        return events
