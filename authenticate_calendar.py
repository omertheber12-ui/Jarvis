"""
Helper script to generate Google Calendar OAuth tokens.

Usage:
    python authenticate_calendar.py

This launches the OAuth consent screen in a browser, saves the resulting
token to `token.json`, and confirms success via stdout.
"""

from src.calendar import GoogleCalendarProvider


def main():
    provider = GoogleCalendarProvider(allow_interactive_auth=True)
    creds = provider.ensure_authenticated()
    email = creds.id_token.get("email") if creds.id_token else "your account"
    print(f"✓ Google Calendar authorization complete for {email}.")
    print("Tokens saved to token.json.")


if __name__ == "__main__":
    main()
"""
Simple script to authenticate with Google Calendar
Run this once to set up authentication
"""

from src.calendar.google_calendar_provider import GoogleCalendarProvider

print("=" * 60)
print("Google Calendar Authentication")
print("=" * 60)
print()

provider = GoogleCalendarProvider()

if provider.is_authenticated():
    print("✓ Already authenticated with Google Calendar!")
    print("You can now use calendar features in Jarvis.")
else:
    print("Starting authentication process...")
    print()
    
    try:
        success = provider.authenticate()
        if success:
            print()
            print("✓ Authentication successful!")
            print("You can now use calendar features in Jarvis.")
        else:
            print("✗ Authentication failed. Please try again.")
    except Exception as e:
        print(f"✗ Error during authentication: {e}")
        print()
        print("Troubleshooting:")
        print("1. Make sure google_calendar_credentials.json exists")
        print("2. Check that Google Calendar API is enabled in Google Cloud Console")
        print("3. Verify your client ID and secret are correct")


