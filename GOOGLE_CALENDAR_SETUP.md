## Google Calendar Setup

1. **Enable API & download OAuth client**
   - In Google Cloud Console, enable the Calendar API for your project.
   - Create an “OAuth client ID” (Desktop app is simplest during development).
   - Download the JSON and save it as `google_calendar_credentials.json` in the repo root. Make sure it contains `client_id`, `client_secret`, and redirect URIs.

2. **Install dependencies**
   - Already covered in `requirements.txt`: install/update with `pip install -r requirements.txt`.

3. **Generate user tokens**
   - Run `python authenticate_calendar.py`.
   - Sign in with the Google account that owns the calendar.
   - The script saves tokens to `token.json` (refresh tokens included). Keep it private.

4. **Verify connectivity**
   - After authentication, run `python jarvis_chat.py --calendar-test` (added in Feature 2).
   - The script lists the next few events; confirm they match your calendar.

5. **Security notes**
   - Never commit `google_calendar_credentials.json` or `token.json`.
   - Regenerate tokens if you revoke access from the Google Account permissions page.

Refer to `CALENDAR_ARCHITECTURE.md` for a high-level design once available. This document only covers local setup.
# Google Calendar Integration Setup

## Overview

Jarvis now supports Google Calendar integration through OpenAI function calling. The AI can:
- Check calendar status before creating events
- Create, update, and delete calendar events
- View upcoming events
- Detect conflicts automatically

## Architecture Decision

**We chose OpenAI Function Calling over MCP** because:
- ✅ Already supported by GPT-4o-mini
- ✅ No additional infrastructure needed
- ✅ Works seamlessly with our existing architecture
- ✅ Can add MCP later if needed

## Setup Instructions

### 1. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 2. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Google Calendar API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Choose "Desktop app" as application type
4. Name it "Jarvis Calendar"
5. Download the JSON file
6. Save it as `google_calendar_credentials.json` in the project root

### 4. First-Time Authentication

When you first run Jarvis with calendar enabled:

1. The app will prompt you to visit an authorization URL
2. Sign in with your Google account
3. Grant calendar access permissions
4. Copy the authorization code
5. Paste it into the terminal

The token will be saved in `google_calendar_token.pickle` for future use.

### 5. Environment Configuration (Optional)

Add to `.env` file:

```
ENABLE_CALENDAR=true
GOOGLE_CALENDAR_CREDENTIALS_FILE=google_calendar_credentials.json
```

## How It Works

### Calendar Flow

1. **User Request**: "Schedule a meeting tomorrow at 2pm"
2. **AI Detection**: AI detects calendar intent
3. **Calendar Check**: AI calls `check_calendar_status` (automatic)
4. **Conflict Detection**: If conflicts found, AI informs user
5. **Event Creation**: If no conflicts, AI calls `create_calendar_event`
6. **Confirmation**: AI confirms the action to user

### Key Features

- **Always Checks First**: Calendar status is checked before any action (as per requirement)
- **Conflict Detection**: Automatically detects and reports conflicts
- **Natural Language**: AI understands dates/times in natural language
- **Error Handling**: Gracefully handles authentication and API errors

## Calendar Provider Architecture

The system uses a **unified abstraction layer**:

```
CalendarProvider (Abstract)
    ↓
GoogleCalendarProvider (Current)
    ↓
Future: OutlookCalendarProvider, AppleCalendarProvider, etc.
```

This makes it easy to add new calendar providers without changing core logic.

## Testing

Test calendar integration:

1. **Check Calendar**: "What's on my calendar tomorrow?"
2. **Create Event**: "Schedule a meeting tomorrow at 2pm"
3. **View Events**: "Show me my upcoming events"
4. **Conflict Test**: Try scheduling over an existing event

## Troubleshooting

### "Calendar not authenticated"
- Run the authentication flow (see step 4 above)
- Check that `google_calendar_credentials.json` exists

### "Credentials file not found"
- Ensure `google_calendar_credentials.json` is in project root
- Check file name matches exactly

### "API error"
- Verify Google Calendar API is enabled in Cloud Console
- Check internet connection
- Verify OAuth credentials are valid

## Security Notes

- `google_calendar_credentials.json` is in `.gitignore` (never commit)
- `google_calendar_token.pickle` contains your access token (never commit)
- Tokens are stored locally on your machine
- Revoke access in Google Account settings if needed


