# Jarvis - Personal Secretary

Feature 1: Basic Text-Based Conversation with OpenAI API

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key

**Recommended: Use .env file** (easiest and most secure)

1. Copy the example file:
   ```bash
   # Windows PowerShell
   Copy-Item .env.example .env
   
   # Linux/Mac
   cp .env.example .env
   ```

2. Edit `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

3. Get your API key from: https://platform.openai.com/api-keys

**Alternative: Set as environment variable**

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=your-api-key-here
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Run the Application

```bash
python jarvis_chat.py
```

To quickly verify Google Calendar access (Feature 2 groundwork), run:

```bash
python jarvis_chat.py --calendar-test
```

See `GOOGLE_CALENDAR_SETUP.md` for credential instructions.

### 4. Open in Browser

Navigate to: `http://localhost:5000`

## Features

- ✅ Web-based chat interface (Flask)
- ✅ Continuous conversation with context memory
- ✅ Conversation persistence (JSON storage)
- ✅ 400 character message limit
- ✅ Uses GPT-4o-mini model
- ✅ Modular design for easy extension

## Project Structure

```
.
├── jarvis_chat.py              # Main Flask application
├── src/                        # Source modules (config, storage, OpenAI, calendar, etc.)
├── templates/                  # Flask HTML templates
├── scripts/                    # Utility helpers (auth, tests, dev server)
│   ├── authenticate_calendar.py
│   ├── run_tests.py
│   └── test_server.py
├── docs/                       # Additional setup and testing guides
│   ├── INSTALL_PYTHON.md
│   ├── GOOGLE_CALENDAR_SETUP.md
│   └── TESTING.md
├── tests/                      # Pytest suite
├── data/                       # Runtime artifacts (git-ignored JSON/log files)
│   ├── storage/                # conversations.json lives here
│   ├── credentials/            # Google OAuth secrets + tokens
│   └── logs/                   # Application logs
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── .env / .env.example         # Environment variables
└── README.md                   # This file
```

## Modular Design

The code is organized into separate modules for scalability:

- **`src/config.py`**: Configuration constants (message limits, model settings, prompts)
- **`src/storage.py`**: ConversationStorage class - handles JSON file persistence
- **`src/openai_client.py`**: OpenAIClient class - manages OpenAI API communication
- **`src/conversation_manager.py`**: ConversationManager class - orchestrates conversation flow and validation
- **`jarvis_chat.py`**: Flask application with routes

This structure makes it easy to:
- Swap storage (JSON → database) without changing other modules
- Add new features (Google Calendar, tasks) as separate modules
- Test individual components independently
- Scale the project with new features
- Maintain clean separation of concerns

## Next Steps (Feature 2+)

- Google Calendar integration
- Task management
- Voice input/output
- Enhanced conversation features

## Notes

- Conversations are stored in `data/storage/conversations.json`
- Each session maintains full conversation history
- System prompt defines Jarvis's personality
- Error handling for API failures and validation
