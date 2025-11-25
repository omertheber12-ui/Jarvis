"""
Conversation manager - orchestrates conversation flow and validation
"""

import json
from typing import Any, Dict, List

from .calendar import GoogleCalendarProvider
from .storage import ConversationStorage
from .openai_client import OpenAIClient, ModelResponse, ToolRequest
from .tasks import TaskManager
from .config import (
    CALENDAR_TOOLS,
    ENABLE_CALENDAR,
    ENABLE_TASKS,
    MAX_MESSAGE_LENGTH,
    TASK_TOOLS,
)


class ConversationManager:
    """Manages conversation flow, validation, and tool execution."""

    def __init__(self):
        self.storage = ConversationStorage()
        self.api_client = OpenAIClient()
        self.enable_calendar = ENABLE_CALENDAR
        self.enable_tasks = ENABLE_TASKS
        self.calendar = GoogleCalendarProvider() if self.enable_calendar else None
        self.task_manager = TaskManager() if self.enable_tasks else None
        self.max_tool_iterations = 3
        self.tool_handlers: Dict[str, Any] = {}
        self.disabled_tool_messages: Dict[str, str] = {}
        self._register_tool_handlers()
        self._validate_tool_configuration()

    def _register_tool_handlers(self) -> None:
        if self.enable_calendar and self.calendar:
            self.tool_handlers.update(
                {
                    "list_upcoming_events": self._handle_list_events,
                    "check_calendar_status": self._handle_check_calendar_status,
                    "create_calendar_event": self._handle_create_event,
                    "update_calendar_event": self._handle_update_event,
                    "delete_calendar_event": self._handle_delete_event,
                }
            )
        else:
            for name in (
                "list_upcoming_events",
                "check_calendar_status",
                "create_calendar_event",
                "update_calendar_event",
                "delete_calendar_event",
            ):
                self.disabled_tool_messages[name] = (
                    "Calendar features are disabled for this Jarvis instance."
                )

        if self.enable_tasks and self.task_manager:
            self.tool_handlers.update(
                {
                    "create_task": self._handle_create_task,
                    "list_tasks": self._handle_list_tasks,
                    "update_task": self._handle_update_task,
                    "delete_task": self._handle_delete_task,
                    "complete_task": self._handle_complete_task,
                }
            )
        else:
            for name in (
                "create_task",
                "list_tasks",
                "update_task",
                "delete_task",
                "complete_task",
            ):
                self.disabled_tool_messages[name] = (
                    "Task management is disabled for this Jarvis instance."
                )

    @staticmethod
    def _extract_tool_names(tool_definitions):
        names = set()
        for tool in tool_definitions:
            function_block = tool.get("function", {})
            name = function_block.get("name")
            if name:
                names.add(name)
        return names

    def _validate_tool_configuration(self) -> None:
        """Ensure tool metadata and handlers remain in sync."""
        expected_names = set()
        if self.enable_calendar:
            expected_names.update(self._extract_tool_names(CALENDAR_TOOLS))
        if self.enable_tasks:
            expected_names.update(self._extract_tool_names(TASK_TOOLS))

        handler_names = set(self.tool_handlers.keys())
        missing_handlers = expected_names - handler_names
        unexpected_handlers = handler_names - expected_names

        if missing_handlers or unexpected_handlers:
            problems = []
            if missing_handlers:
                problems.append(
                    f"Missing handlers for tools: {sorted(missing_handlers)}"
                )
            if unexpected_handlers:
                problems.append(
                    f"Handlers registered without tool metadata: {sorted(unexpected_handlers)}"
                )
            raise RuntimeError(
                "Tool configuration mismatch detected. " + " ".join(problems)
            )

    def validate_message(self, message: str):
        """Validate message length"""
        if not message or not message.strip():
            return False, "Message cannot be empty"
        if len(message) > MAX_MESSAGE_LENGTH:
            return False, f"Message exceeds {MAX_MESSAGE_LENGTH} character limit"
        return True, None

    def process_message(self, session_id: str, user_message: str):
        """Process user message and get Jarvis response"""
        is_valid, error = self.validate_message(user_message)
        if not is_valid:
            return None, error

        session = self.storage.get_or_create_session(session_id)
        messages = session["messages"].copy()

        user_entry = {"role": "user", "content": user_message}
        messages.append(user_entry)
        self.storage.add_message(session_id, "user", user_message)

        try:
            response_text = self._run_conversation_loop(session_id, messages)
            return response_text, None
        except RuntimeError as exc:
            return None, self._format_error_message(str(exc))
        except Exception as exc:  # pylint: disable=broad-except
            return None, "Jarvis ran into an unexpected error. " + str(exc)

    def _run_conversation_loop(
        self, session_id: str, messages: List[Dict[str, Any]]
    ) -> str:
        for _ in range(self.max_tool_iterations):
            ai_response: ModelResponse = self.api_client.get_response(messages)
            assistant_message = ai_response.message

            extra_fields = {
                key: value
                for key, value in assistant_message.items()
                if key not in {"role", "content"}
            }
            messages.append(assistant_message)
            self.storage.add_message(
                session_id,
                assistant_message.get("role", "assistant"),
                assistant_message.get("content"),
                **extra_fields,
            )

            if ai_response.tool_calls:
                self._handle_tool_calls(session_id, messages, ai_response.tool_calls)
                continue

            if ai_response.content:
                return ai_response.content

            break
        raise RuntimeError(
            "Unable to complete the response after handling tool calls. Please try again."
        )

    def _handle_tool_calls(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        tool_calls: List[ToolRequest],
    ) -> None:
        for tool_call in tool_calls:
            result = self._execute_tool(tool_call)
            tool_content = json.dumps(result, ensure_ascii=False)
            tool_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.name,
                "content": tool_content,
            }
            messages.append(tool_message)
            self.storage.add_message(
                session_id,
                "tool",
                tool_content,
                tool_call_id=tool_call.id,
                name=tool_call.name,
            )

    def _execute_tool(self, tool_call: ToolRequest) -> Dict[str, Any]:
        disabled_message = self.disabled_tool_messages.get(tool_call.name)
        if disabled_message:
            return {"success": False, "error": disabled_message}
        handler = self.tool_handlers.get(tool_call.name)
        if not handler:
            return {"success": False, "error": f"Unsupported tool: {tool_call.name}"}
        try:
            result = handler(tool_call.arguments)
            return {"success": True, "result": result}
        except Exception as exc:  # pylint: disable=broad-except
            return {"success": False, "error": str(exc)}

    def _handle_list_events(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        max_results = int(arguments.get("max_results", 5) or 5)
        max_results = max(1, min(max_results, 20))
        events = self.calendar.list_upcoming_events(max_results=max_results)
        return {"events": [event.to_dict() for event in events]}

    def _handle_check_calendar_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        start_time = arguments.get("start_time")
        end_time = arguments.get("end_time")
        if not start_time or not end_time:
            raise ValueError(
                "Both start_time and end_time are required for availability checks."
            )
        events = self.calendar.list_events_in_range(start_time, end_time)
        return {
            "conflicts": [event.to_dict() for event in events],
            "is_available": len(events) == 0,
        }

    def _handle_create_event(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        summary = arguments.get("summary")
        start_time = arguments.get("start_time")
        end_time = arguments.get("end_time")
        if not all([summary, start_time, end_time]):
            raise ValueError(
                "summary, start_time, and end_time are required to create events."
            )

        conflicts = self.calendar.list_events_in_range(start_time, end_time)
        if conflicts:
            return {
                "created": False,
                "conflicts": [event.to_dict() for event in conflicts],
                "message": "Timeslot is unavailable.",
            }

        event = self.calendar.create_event(
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            description=arguments.get("description"),
            location=arguments.get("location"),
        )
        return {"created": True, "event": event.to_dict()}

    def _handle_update_event(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        event_id = arguments.get("event_id")
        if not event_id:
            raise ValueError("event_id is required to update an event.")
        event = self.calendar.update_event(
            event_id=event_id,
            summary=arguments.get("summary"),
            start_time=arguments.get("start_time"),
            end_time=arguments.get("end_time"),
            description=arguments.get("description"),
            location=arguments.get("location"),
        )
        return {"event": event.to_dict()}

    def _handle_delete_event(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        event_id = arguments.get("event_id")
        if not event_id:
            raise ValueError("event_id is required to delete an event.")
        self.calendar.delete_event(event_id)
        return {"deleted": True, "event_id": event_id}

    def _handle_create_task(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        title = arguments.get("title")
        if not title:
            raise ValueError("title is required to create a task.")
        task = self.task_manager.create_task(
            title=title,
            description=arguments.get("description"),
            due_date=arguments.get("due_date"),
            priority=arguments.get("priority", "normal"),
        )
        return {"task": task}

    def _handle_list_tasks(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        tasks = self.task_manager.list_tasks(
            status=arguments.get("status"),
            priority=arguments.get("priority"),
        )
        return {"tasks": tasks, "count": len(tasks)}

    def _handle_update_task(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        task_id = arguments.get("task_id")
        if not task_id:
            raise ValueError("task_id is required to update a task.")
        task = self.task_manager.update_task(
            task_id=task_id,
            title=arguments.get("title"),
            description=arguments.get("description"),
            due_date=arguments.get("due_date"),
            priority=arguments.get("priority"),
        )
        return {"task": task}

    def _handle_delete_task(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        task_id = arguments.get("task_id")
        if not task_id:
            raise ValueError("task_id is required to delete a task.")
        self.task_manager.delete_task(task_id)
        return {"deleted": True, "task_id": task_id}

    def _handle_complete_task(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        task_id = arguments.get("task_id")
        if not task_id:
            raise ValueError("task_id is required to complete a task.")
        task = self.task_manager.complete_task(task_id)
        return {"task": task}

    def _format_error_message(self, error_text: str) -> str:
        lowered = error_text.lower()
        if "google calendar" in lowered:
            return (
                "I couldn't access Google Calendar. Please re-run the calendar "
                "authentication helper or verify ENABLE_CALENDAR is true."
            )
        return error_text

