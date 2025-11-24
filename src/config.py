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

# Storage configuration
STORAGE_FILE = Path(os.getenv("STORAGE_FILE", STORAGE_DIR / "conversations.json"))

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

