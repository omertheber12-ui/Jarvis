"""
Configuration constants for Jarvis application
Loads environment variables from .env file
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Message constraints
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", 400))

# Storage configuration
STORAGE_FILE = os.getenv("STORAGE_FILE", "conversations.json")

# System prompt for Jarvis
SYSTEM_PROMPT = """You are Jarvis, a helpful personal AI assistant. 
You communicate concisely, ask clarifying questions when needed, and help the user manage tasks and decisions. 
Keep your tone supportive and efficient."""

# OpenAI model configuration
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.7))

# OpenAI API Key (required)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

