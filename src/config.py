"""
Configuration constants for Jarvis application
Loads environment variables from .env file
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("JARVIS_DATA_DIR", BASE_DIR / "data"))
STORAGE_DIR = Path(os.getenv("JARVIS_STORAGE_DIR", DATA_DIR / "storage"))
CREDENTIALS_DIR = Path(
    os.getenv("JARVIS_CREDENTIALS_DIR", DATA_DIR / "credentials")
)
LOG_DIR = Path(os.getenv("JARVIS_LOG_DIR", DATA_DIR / "logs"))

# Message constraints
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", 400))

# Helpers
def _env_bool(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Storage configuration
STORAGE_FILE = Path(os.getenv("STORAGE_FILE", STORAGE_DIR / "conversations.json"))
TASKS_FILE = Path(os.getenv("TASKS_FILE", STORAGE_DIR / "tasks.json"))

# System prompt for Jarvis
SYSTEM_PROMPT = """You are Jarvis, a helpful personal AI assistant. 
You communicate concisely, ask clarifying questions when needed, and help the user manage tasks and decisions. 
Keep your tone supportive and efficient."""

# OpenAI model configuration
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.7))

# OpenAI API Key (required)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Google Calendar files
GOOGLE_CREDENTIALS_FILE = Path(
    os.getenv(
        "GOOGLE_CREDENTIALS_FILE",
        CREDENTIALS_DIR / "google_calendar_credentials.json",
    )
)
GOOGLE_TOKEN_FILE = Path(
    os.getenv("GOOGLE_TOKEN_FILE", CREDENTIALS_DIR / "token.json")
)

# Logging
LOG_FILE = Path(os.getenv("LOG_FILE", LOG_DIR / "jarvis.log"))
API_LOG_FILE = Path(os.getenv("API_LOG_FILE", LOG_DIR / "api_calls.log"))

# OpenAI tool definitions (Stage 1 - Calendar)
CALENDAR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_upcoming_events",
            "description": "List upcoming events on your Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of events to return (default 5, max 20).",
                        "minimum": 1,
                        "maximum": 20,
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_calendar_status",
            "description": "Check availability and list events in a specific time window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "description": "ISO-8601 start timestamp (e.g., 2024-05-01T09:00:00-04:00).",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "ISO-8601 end timestamp.",
                    },
                },
                "required": ["start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": "Create a new Google Calendar event after confirming availability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Event title."},
                    "start_time": {
                        "type": "string",
                        "description": "ISO-8601 start timestamp.",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "ISO-8601 end timestamp.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional details or agenda.",
                    },
                    "location": {
                        "type": "string",
                        "description": "Optional meeting location or call link.",
                    },
                },
                "required": ["summary", "start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_calendar_event",
            "description": "Update an existing calendar event's time or details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "ID of the event to update."},
                    "summary": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                    "description": {"type": "string"},
                    "location": {"type": "string"},
                },
                "required": ["event_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_calendar_event",
            "description": "Delete a calendar event by ID (requires explicit user confirmation).",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "ID of the event to delete."}
                },
                "required": ["event_id"],
            },
        },
    },
]

TASK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new personal task with optional due date and priority.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short task title."},
                    "description": {"type": "string"},
                    "due_date": {
                        "type": "string",
                        "description": "Optional due date in ISO-8601 format.",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority label (low, normal, high).",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List tasks with optional status or priority filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status (pending or completed).",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Filter by priority (low, normal, high).",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update a task's title, description, due date, or priority.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "ID of the task."},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "due_date": {"type": "string"},
                    "priority": {"type": "string"},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "ID of the task."}
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a task as completed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "ID of the task."}
                },
                "required": ["task_id"],
            },
        },
    },
]

# Feature flags
ENABLE_CALENDAR = _env_bool("ENABLE_CALENDAR", True)
ENABLE_TASKS = _env_bool("ENABLE_TASKS", True)
ENABLE_LOGGING = _env_bool("ENABLE_LOGGING", True)

