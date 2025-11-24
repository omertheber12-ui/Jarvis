"""
Conversation storage handler - manages persistence in JSON format
"""

import json
from datetime import datetime
from pathlib import Path
from .config import STORAGE_FILE, SYSTEM_PROMPT


class ConversationStorage:
    """Handles conversation persistence in JSON format"""
    
    def __init__(self, storage_file=STORAGE_FILE):
        self.storage_file = storage_file
        self.ensure_storage_file()
    
    def ensure_storage_file(self):
        """Create storage file if it doesn't exist"""
        storage_path = Path(self.storage_file)
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not storage_path.exists():
            self.save_conversations({"conversations": []})
    
    def load_conversations(self):
        """Load all conversations from JSON file"""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"conversations": []}
    
    def save_conversations(self, data):
        """Save conversations to JSON file"""
        storage_path = Path(self.storage_file)
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        with storage_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_or_create_session(self, session_id):
        """Get existing session or create new one"""
        data = self.load_conversations()
        
        # Find existing session
        for conv in data["conversations"]:
            if conv["session_id"] == session_id:
                return conv
        
        # Create new session
        new_session = {
            "session_id": session_id,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}],
            "created_at": datetime.now().isoformat()
        }
        data["conversations"].append(new_session)
        self.save_conversations(data)
        return new_session
    
    def add_message(self, session_id, role, content):
        """Add a message to a conversation session"""
        data = self.load_conversations()
        
        for conv in data["conversations"]:
            if conv["session_id"] == session_id:
                conv["messages"].append({"role": role, "content": content})
                conv["updated_at"] = datetime.now().isoformat()
                self.save_conversations(data)
                return
        
        # Session not found, create it
        new_session = {
            "session_id": session_id,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": role, "content": content}
            ],
            "created_at": datetime.now().isoformat()
        }
        data["conversations"].append(new_session)
        self.save_conversations(data)

