"""
JSON-backed storage for Jarvis task management.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from ..config import TASKS_FILE


class TaskStorage:
    """Handles persistence of user tasks."""

    def __init__(self, storage_file: Path | str = TASKS_FILE):
        self.storage_file = Path(storage_file)
        self.ensure_storage_file()

    def ensure_storage_file(self) -> None:
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_file.exists():
            self.save_tasks({"tasks": []})

    def load_tasks(self) -> Dict[str, List[Dict]]:
        try:
            with self.storage_file.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"tasks": []}

    def save_tasks(self, data: Dict[str, List[Dict]]) -> None:
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        with self.storage_file.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)

    def get_tasks(self) -> List[Dict]:
        data = self.load_tasks()
        return data.get("tasks", [])

    def write_tasks(self, tasks: List[Dict]) -> None:
        self.save_tasks({"tasks": tasks})

