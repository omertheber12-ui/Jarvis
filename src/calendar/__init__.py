"""
Calendar integration package.

Feature 2 introduces Google Calendar support; modules here encapsulate
API-facing logic so the rest of the app can remain provider-agnostic.
"""

from .google_calendar_provider import GoogleCalendarProvider  # noqa: F401
