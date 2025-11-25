"""
Conversation manager - orchestrates conversation flow and validation
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

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
from .time_utils import format_human, now_local, resolve_time_reference, is_late_hour

DATE_CONFIDENCE_THRESHOLD = 0.98


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
            runtime_messages = messages.copy()
            runtime_messages.append(self._build_time_context_message())
            response_text = self._run_conversation_loop(
                session_id, messages, runtime_messages
            )
            return response_text, None
        except RuntimeError as exc:
            return None, self._format_error_message(str(exc))
        except Exception as exc:  # pylint: disable=broad-except
            return None, "Jarvis ran into an unexpected error. " + str(exc)

    def _run_conversation_loop(
        self,
        session_id: str,
        persistent_messages: List[Dict[str, Any]],
        runtime_messages: List[Dict[str, Any]],
    ) -> str:
        for _ in range(self.max_tool_iterations):
            ai_response: ModelResponse = self.api_client.get_response(runtime_messages)
            assistant_message = ai_response.message

            extra_fields = {
                key: value
                for key, value in assistant_message.items()
                if key not in {"role", "content"}
            }
            persistent_messages.append(assistant_message)
            runtime_messages.append(assistant_message)
            self.storage.add_message(
                session_id,
                assistant_message.get("role", "assistant"),
                assistant_message.get("content"),
                **extra_fields,
            )

            if ai_response.tool_calls:
                self._handle_tool_calls(
                    session_id, persistent_messages, runtime_messages, ai_response.tool_calls
                )
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
        persistent_messages: List[Dict[str, Any]],
        runtime_messages: List[Dict[str, Any]],
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
            persistent_messages.append(tool_message)
            runtime_messages.append(tool_message)
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

    def _ensure_confident_times(
        self,
        arguments: Dict[str, Any],
        required_fields: List[str],
        optional_fields: Optional[List[str]] = None,
    ) -> Tuple[Optional[Dict[str, Dict[str, Any]]], Optional[Dict[str, Any]]]:
        optional_fields = optional_fields or []
        normalized: Dict[str, Dict[str, Any]] = {}
        issues: List[str] = []

        for field in required_fields + optional_fields:
            raw_value = arguments.get(field)
            if raw_value in (None, ""):
                if field in required_fields:
                    issues.append(f"{field} is required.")
                continue

            resolution = resolve_time_reference(str(raw_value))
            if not resolution.iso:
                issues.append(f"{field} could not be interpreted from '{raw_value}'.")
                continue

            localized = datetime.fromisoformat(resolution.iso)
            normalized[field] = {
                "iso": resolution.iso,
                "human": format_human(localized),
                "confidence": resolution.confidence,
                "is_relative": resolution.is_relative,
                "raw": raw_value,
                "late_hour": is_late_hour(localized),
            }

            if resolution.confidence < DATE_CONFIDENCE_THRESHOLD:
                issues.append(
                    f"{field} confidence {resolution.confidence:.2f} below required threshold."
                )
            if is_late_hour(localized):
                issues.append(f"{field} occurs late in the day; confirm with the client.")

        if issues:
            return None, self._build_confirmation_error(issues, normalized)
        return normalized, None

    def _build_confirmation_error(
        self, issues: List[str], normalized: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "DATE_CONFIRMATION_REQUIRED",
            "details": {
                "issues": issues,
                "resolved_values": {
                    field: {
                        "raw": info["raw"],
                        "interpreted": info["human"],
                        "confidence": info["confidence"],
                    }
                    for field, info in normalized.items()
                },
            },
        }

    def _summarize_resolutions(
        self, normalized: Optional[Dict[str, Dict[str, Any]]]
    ) -> Dict[str, Dict[str, str]]:
        if not normalized:
            return {}
        return {
            field: {"iso": info["iso"], "human": info["human"]}
            for field, info in normalized.items()
        }

    def _handle_list_events(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        max_results = int(arguments.get("max_results", 5) or 5)
        max_results = max(1, min(max_results, 20))
        events = self.calendar.list_upcoming_events(max_results=max_results)
        return {"events": [event.to_dict() for event in events]}

    def _handle_check_calendar_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        normalized, error_payload = self._ensure_confident_times(
            arguments, required_fields=["start_time", "end_time"]
        )
        if error_payload:
            return error_payload

        start_time = normalized["start_time"]["iso"]
        end_time = normalized["end_time"]["iso"]

        events = self.calendar.list_events_in_range(start_time, end_time)
        return {
            "conflicts": [event.to_dict() for event in events],
            "is_available": len(events) == 0,
            "resolved_times": self._summarize_resolutions(normalized),
        }

    def _handle_create_event(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        summary = arguments.get("summary")
        if not summary:
            raise ValueError(
                "summary, start_time, and end_time are required to create events."
            )

        normalized, error_payload = self._ensure_confident_times(
            arguments, required_fields=["start_time", "end_time"]
        )
        if error_payload:
            return error_payload

        start_time = normalized["start_time"]["iso"]
        end_time = normalized["end_time"]["iso"]

        conflicts = self.calendar.list_events_in_range(start_time, end_time)
        if conflicts:
            return {
                "created": False,
                "conflicts": [event.to_dict() for event in conflicts],
                "message": "Timeslot is unavailable.",
                "resolved_times": self._summarize_resolutions(normalized),
            }

        event = self.calendar.create_event(
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            description=arguments.get("description"),
            location=arguments.get("location"),
        )
        verified = self.calendar.get_event(event.event_id) if event.event_id else None
        event_payload = self._event_to_dict(event)
        return {
            "created": True,
            "event": event_payload,
            "resolved_times": self._summarize_resolutions(normalized),
            "verification": self._event_to_dict(verified),
        }

    def _handle_update_event(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        event_id = arguments.get("event_id")
        if not event_id:
            raise ValueError("event_id is required to update an event.")

        normalized, error_payload = self._ensure_confident_times(
            arguments, required_fields=[], optional_fields=["start_time", "end_time"]
        )
        if error_payload:
            return error_payload

        event = self.calendar.update_event(
            event_id=event_id,
            summary=arguments.get("summary"),
            start_time=normalized.get("start_time", {}).get("iso"),
            end_time=normalized.get("end_time", {}).get("iso"),
            description=arguments.get("description"),
            location=arguments.get("location"),
        )
        result = {"event": self._event_to_dict(event)}
        if normalized:
            result["resolved_times"] = self._summarize_resolutions(normalized)
        verified = self.calendar.get_event(event.event_id or event_id)
        result["verification"] = self._event_to_dict(verified)
        return result

    def _handle_delete_event(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        event_id = arguments.get("event_id")
        if not event_id:
            raise ValueError("event_id is required to delete an event.")
        self.calendar.delete_event(event_id)
        post_state = self.calendar.get_event(event_id)
        return {
            "deleted": True,
            "event_id": event_id,
            "verified_deleted": post_state is None,
        }

    def _handle_create_task(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        title = arguments.get("title")
        if not title:
            raise ValueError("title is required to create a task.")
        normalized, error_payload = self._ensure_confident_times(
            arguments, required_fields=[], optional_fields=["due_date"]
        )
        if error_payload:
            return error_payload
        task = self.task_manager.create_task(
            title=title,
            description=arguments.get("description"),
            due_date=normalized.get("due_date", {}).get("iso"),
            priority=arguments.get("priority", "normal"),
        )
        result = {"task": task}
        if normalized:
            result["resolved_times"] = self._summarize_resolutions(normalized)
        return result

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
        normalized, error_payload = self._ensure_confident_times(
            arguments, required_fields=[], optional_fields=["due_date"]
        )
        if error_payload:
            return error_payload
        task = self.task_manager.update_task(
            task_id=task_id,
            title=arguments.get("title"),
            description=arguments.get("description"),
            due_date=normalized.get("due_date", {}).get("iso")
            if normalized
            else arguments.get("due_date"),
            priority=arguments.get("priority"),
        )
        result = {"task": task}
        if normalized:
            result["resolved_times"] = self._summarize_resolutions(normalized)
        return result

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

    def _build_time_context_message(self) -> Dict[str, str]:
        timestamp_text = format_human(now_local())
        return {
            "role": "system",
            "content": (
                f"Reference date/time: {timestamp_text}. "
                "Interpret relative date phrases based on this moment."
            ),
        }

    @staticmethod
    def _event_to_dict(event: Any) -> Optional[Dict[str, Any]]:
        if event is None:
            return None
        if isinstance(event, dict):
            return event
        if hasattr(event, "to_dict"):
            return event.to_dict()
        fallback: Dict[str, Any] = {}
        for attr in ("event_id", "summary", "start", "end"):
            if hasattr(event, attr):
                value = getattr(event, attr)
                fallback[attr] = (
                    value
                    if isinstance(value, (str, int, float, bool))
                    else str(value)
                )
        if not fallback:
            fallback["representation"] = repr(event)
        return fallback

