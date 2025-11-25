"""
OpenAI API client - handles communication with OpenAI API
"""

import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Dict, List, Optional

from openai import OpenAI

from .api_logger import api_logger
from .config import (
    CALENDAR_TOOLS,
    ENABLE_CALENDAR,
    ENABLE_TASKS,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    OPENAI_API_KEY,
    TASK_TOOLS,
)


@dataclass
class ToolRequest:
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ModelResponse:
    content: Optional[str]
    tool_calls: List[ToolRequest]
    message: Dict[str, Any]
    finish_reason: Optional[str]


class OpenAIClient:
    """Handles communication with OpenAI API"""

    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please check your .env file or environment variables."
            )
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        self.temperature = OPENAI_TEMPERATURE
        self.tools: List[Dict[str, Any]] = []
        if ENABLE_CALENDAR:
            self.tools.extend(CALENDAR_TOOLS)
        if ENABLE_TASKS:
            self.tools.extend(TASK_TOOLS)

    def get_response(self, messages: List[Dict[str, Any]]) -> ModelResponse:
        """Send messages to OpenAI and get response"""
        request_summary = self._build_request_summary(messages)
        start = perf_counter()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                tools=self.tools if self.tools else None,
                tool_choice="auto" if self.tools else "none",
            )
            choice = response.choices[0]
            message = choice.message
            tool_calls = self._extract_tool_calls(message)
            assistant_message = self._message_to_dict(message)
            content = message.content if isinstance(message.content, str) else None
            duration_ms = int((perf_counter() - start) * 1000)
            api_logger.log_call(
                service="openai",
                action="chat.completions.create",
                request=request_summary,
                response={
                    "choice_count": len(response.choices),
                    "finish_reason": getattr(choice, "finish_reason", None),
                    "tool_call_count": len(tool_calls),
                    "content_preview": (content[:200] if content else None),
                },
                metadata={"duration_ms": duration_ms},
            )
            return ModelResponse(
                content=content,
                tool_calls=tool_calls,
                message=assistant_message,
                finish_reason=getattr(choice, "finish_reason", None),
            )
        except Exception as e:
            duration_ms = int((perf_counter() - start) * 1000)
            api_logger.log_call(
                service="openai",
                action="chat.completions.create",
                request=request_summary,
                error=str(e),
                metadata={"duration_ms": duration_ms},
            )
            raise Exception(f"OpenAI API error: {str(e)}")

    def _build_request_summary(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        summary = {
            "message_count": len(messages or []),
            "roles": [msg.get("role") for msg in messages],
            "tools_enabled": bool(self.tools),
        }
        if messages:
            last_message = messages[-1].get("content", "")
            summary["last_message_preview"] = last_message[:200]
        return summary

    def _extract_tool_calls(self, message) -> List[ToolRequest]:
        tool_calls: List[ToolRequest] = []
        if not getattr(message, "tool_calls", None):
            return tool_calls
        for tool_call in message.tool_calls:
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
            tool_calls.append(
                ToolRequest(
                    id=tool_call.id,
                    name=tool_call.function.name,
                    arguments=arguments,
                )
            )
        return tool_calls

    def _message_to_dict(self, message) -> Dict[str, Any]:
        assistant_message = {
            "role": message.role,
            "content": message.content,
        }
        if getattr(message, "tool_calls", None):
            assistant_message["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
                for tool_call in message.tool_calls
            ]
        return assistant_message

