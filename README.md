<<<<<<< HEAD
# Jarvis - Personal Secretary

Feature 1: Basic Text-Based Conversation with OpenAI API
=======
# Jarvis - Personal Secretary

Feature 1: Basic Text-Based Conversation with OpenAI API

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key

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

**Or create a `.env` file** (optional, requires python-dotenv):
```
OPENAI_API_KEY=your-api-key-here
```

### 3. Run the Application

```bash
python jarvis_chat.py
```

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
├── jarvis_chat.py          # Main Flask application
├── src/                    # Source modules
│   ├── __init__.py
│   ├── config.py           # Configuration constants
│   ├── storage.py          # ConversationStorage class
│   ├── openai_client.py    # OpenAIClient class
│   └── conversation_manager.py  # ConversationManager class
├── templates/
│   └── index.html          # Chat UI
├── conversations.json      # Conversation storage (auto-created)
├── requirements.txt        # Python dependencies
└── README.md              # This file
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

- Conversations are stored in `conversations.json`
- Each session maintains full conversation history
- System prompt defines Jarvis's personality
- Error handling for API failures and validation

>>>>>>> master
