"""
Helper script to generate Google Calendar OAuth tokens.

Usage:
    python scripts/authenticate_calendar.py

This launches the OAuth consent screen in a browser, saves the resulting
token to `data/credentials/token.json`, and confirms success via stdout.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.calendar import GoogleCalendarProvider


def main():
    provider = GoogleCalendarProvider(allow_interactive_auth=True)
    creds = provider.ensure_authenticated()
    email = creds.id_token.get("email") if creds.id_token else "your account"
    print(f"✓ Google Calendar authorization complete for {email}.")
    print("Tokens saved to data/credentials/token.json.")


if __name__ == "__main__":
    main()
