"""
Configuration constants for Jarvis application
"""

# Message constraints
MAX_MESSAGE_LENGTH = 400

# Storage configuration
STORAGE_FILE = "conversations.json"

# System prompt for Jarvis
SYSTEM_PROMPT = """You are Jarvis, a helpful personal AI assistant. 
You communicate concisely, ask clarifying questions when needed, and help the user manage tasks and decisions. 
Keep your tone supportive and efficient."""

# OpenAI model configuration
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.7

