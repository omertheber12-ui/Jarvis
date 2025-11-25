"""
High-level task management helpers built on TaskStorage.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from .task_storage import TaskStorage

VALID_PRIORITIES = {"low", "normal", "high"}
VALID_STATUSES = {"pending", "completed"}


class TaskManager:
    """Business logic for creating and maintaining personal tasks."""

    def __init__(self, storage: Optional[TaskStorage] = None):
        self.storage = storage or TaskStorage()

    def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: str = "normal",
    ) -> Dict:
        timestamp = datetime.now(timezone.utc).isoformat()
        task = {
            "id": str(uuid4()),
            "title": title.strip(),
            "description": (description or "").strip() or None,
            "due_date": due_date,
            "priority": self._normalize_priority(priority),
            "status": "pending",
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        tasks = self.storage.get_tasks()
        tasks.append(task)
        self.storage.write_tasks(tasks)
        return task

    def list_tasks(
        self, status: Optional[str] = None, priority: Optional[str] = None
    ) -> List[Dict]:
        tasks = self.storage.get_tasks()
        if status:
            status = status.lower()
            tasks = [task for task in tasks if task.get("status") == status]
        if priority:
            priority = priority.lower()
            tasks = [task for task in tasks if task.get("priority") == priority]
        return tasks

    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict:
        tasks = self.storage.get_tasks()
        for task in tasks:
            if task["id"] == task_id:
                if title is not None:
                    task["title"] = title.strip()
                if description is not None:
                    task["description"] = description.strip() or None
                if due_date is not None:
                    task["due_date"] = due_date
                if priority is not None:
                    task["priority"] = self._normalize_priority(priority)
                if status is not None:
                    task["status"] = self._normalize_status(status)
                task["updated_at"] = datetime.now(timezone.utc).isoformat()
                self.storage.write_tasks(tasks)
                return task
        raise ValueError(f"Task with id '{task_id}' was not found.")

    def delete_task(self, task_id: str) -> None:
        tasks = self.storage.get_tasks()
        filtered = [task for task in tasks if task["id"] != task_id]
        if len(filtered) == len(tasks):
            raise ValueError(f"Task with id '{task_id}' was not found.")
        self.storage.write_tasks(filtered)

    def complete_task(self, task_id: str) -> Dict:
        return self.update_task(task_id, status="completed")

    def _normalize_priority(self, value: Optional[str]) -> str:
        if not value:
            return "normal"
        value = value.lower()
        if value not in VALID_PRIORITIES:
            return "normal"
        return value

    def _normalize_status(self, value: str) -> str:
        value = value.lower()
        if value not in VALID_STATUSES:
            raise ValueError(f"Unsupported status '{value}'.")
        return value

