"""Tests for task manager module."""

import os
import tempfile

import pytest

from src.tasks.task_manager import TaskManager
from src.tasks.task_storage import TaskStorage


class TestTaskManager:
    def setup_method(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        storage = TaskStorage(storage_file=self.temp_file.name)
        self.manager = TaskManager(storage=storage)

    def teardown_method(self):
        os.unlink(self.temp_file.name)

    def test_create_task_defaults(self):
        task = self.manager.create_task("Buy groceries")
        assert task["title"] == "Buy groceries"
        assert task["priority"] == "normal"
        assert task["status"] == "pending"

    def test_list_tasks_with_filters(self):
        self.manager.create_task("Task A", priority="low")
        task_b = self.manager.create_task("Task B", priority="high")
        self.manager.complete_task(task_b["id"])

        high_tasks = self.manager.list_tasks(priority="high")
        assert len(high_tasks) == 1
        assert high_tasks[0]["title"] == "Task B"

        completed = self.manager.list_tasks(status="completed")
        assert len(completed) == 1

    def test_update_task(self):
        task = self.manager.create_task("Draft email")
        updated = self.manager.update_task(
            task["id"], title="Draft longer email", priority="high"
        )
        assert updated["title"] == "Draft longer email"
        assert updated["priority"] == "high"

    def test_delete_task(self):
        task = self.manager.create_task("Temporary task")
        self.manager.delete_task(task["id"])
        remaining = self.manager.list_tasks()
        assert remaining == []

    def test_complete_task(self):
        task = self.manager.create_task("Call client")
        completed = self.manager.complete_task(task["id"])
        assert completed["status"] == "completed"

    def test_update_invalid_task_raises(self):
        with pytest.raises(ValueError):
            self.manager.update_task("missing", title="Nope")
