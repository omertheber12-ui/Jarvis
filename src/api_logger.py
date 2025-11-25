"""
Centralized logging utilities for external API calls.
"""

from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Optional

from .config import ENABLE_LOGGING, LOG_DIR, API_LOG_FILE

MAX_FIELD_LENGTH = 2000


class ApiLogger:
    """JSON-line logger that records every outbound API interaction."""

    def __init__(self) -> None:
        self.enabled = ENABLE_LOGGING
        self._lock = Lock()
        self._logger = logging.getLogger("jarvis.api_calls")
        self._fallback_logger = logging.getLogger("jarvis.api_fallback")
        self._disabled_warning_emitted = False
        self._last_disabled_error: Optional[str] = None
        if self.enabled:
            if not self._logger.handlers:
                self._configure_logger()
            self._logger.setLevel(logging.INFO)
            self._logger.propagate = False

    def _configure_logger(self) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        API_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        handler = RotatingFileHandler(
            API_LOG_FILE,
            maxBytes=1_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        self._logger.addHandler(handler)

    def log_call(
        self,
        *,
        service: str,
        action: str,
        request: Optional[Any] = None,
        response: Optional[Any] = None,
        error: Optional[str] = None,
        metadata: Optional[Any] = None,
    ) -> None:
        """Write a normalized log entry for an external API call."""
        if not self.enabled:
            if error:
                self._last_disabled_error = str(error)
                if not self._disabled_warning_emitted:
                    self._fallback_logger.warning(
                        "API logging disabled; first error captured from %s.%s: %s",
                        service,
                        action,
                        self._last_disabled_error,
                    )
                    self._disabled_warning_emitted = True
            return
        entry = {
            "timestamp": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            "service": service,
            "action": action,
            "request": self._prepare_payload(request),
            "response": self._prepare_payload(response),
            "error": error if error is None else str(error),
            "metadata": self._prepare_payload(metadata),
        }
        serialized = json.dumps(entry, ensure_ascii=False)
        with self._lock:
            self._logger.info(serialized)

    def _prepare_payload(self, payload: Any) -> Any:
        """Sanitize payloads so they are JSON serializable and bounded."""
        if payload is None:
            return None

        if isinstance(payload, (int, float, bool)):
            return payload

        if isinstance(payload, str):
            return self._truncate(payload)

        if isinstance(payload, dict):
            return {
                str(key): self._prepare_payload(value) for key, value in payload.items()
            }

        if isinstance(payload, (list, tuple)):
            return [self._prepare_payload(item) for item in payload]

        try:
            serialized = json.loads(json.dumps(payload, default=str))
        except Exception:
            serialized = str(payload)

        if isinstance(serialized, str):
            return self._truncate(serialized)
        return serialized

    def _truncate(self, value: str) -> str:
        if len(value) <= MAX_FIELD_LENGTH:
            return value
        return f"{value[:MAX_FIELD_LENGTH]}...(truncated)"

    @property
    def last_disabled_error(self) -> Optional[str]:
        return self._last_disabled_error


api_logger = ApiLogger()


