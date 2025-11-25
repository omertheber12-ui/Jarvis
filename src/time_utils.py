"""
Helpers for working with local time references and relative phrases.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .config import CLIENT_TIMEZONE


try:
    LOCAL_ZONE = ZoneInfo(CLIENT_TIMEZONE)
except ZoneInfoNotFoundError:
    # Fallback to UTC+2 if tzdata is not available in the environment.
    LOCAL_ZONE = timezone(timedelta(hours=2))
LATE_HOUR_THRESHOLD = 21

RELATIVE_KEYWORDS = (
    ("day after tomorrow", 2),
    ("tomorrow", 1),
    ("today", 0),
    ("tonight", 0),
)

TIME_PATTERN = re.compile(
    r"(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<ampm>am|pm)?", re.IGNORECASE
)


@dataclass
class TimeResolution:
    """Represents the outcome of attempting to resolve a time reference."""

    iso: Optional[str]
    confidence: float
    source_text: str
    is_relative: bool


def now_local() -> datetime:
    return datetime.now(LOCAL_ZONE)


def format_human(dt: datetime) -> str:
    localized = dt.astimezone(LOCAL_ZONE)
    return localized.strftime("%A, %d %B %Y, %H:%M")


def is_late_hour(dt: datetime) -> bool:
    localized = dt.astimezone(LOCAL_ZONE)
    return localized.hour >= LATE_HOUR_THRESHOLD


def resolve_time_reference(value: Optional[str], reference: Optional[datetime] = None) -> TimeResolution:
    """
    Attempt to turn an arbitrary string into an ISO timestamp plus confidence level.

    Confidence scale:
        1.0  = explicit ISO timestamp with date and time
        0.9  = relative term with explicit time (e.g., "tomorrow 3pm")
        0.6  = relative term without explicit time (defaults to 09:00)
        0.0  = unable to interpret
    """
    if not value:
        return TimeResolution(None, 0.0, value or "", False)

    reference = reference or now_local()
    trimmed = value.strip()

    iso_result = _try_parse_iso(trimmed)
    if iso_result:
        return TimeResolution(iso_result.isoformat(), 1.0, trimmed, False)

    relative_result = _try_parse_relative(trimmed.lower(), reference)
    if relative_result:
        return relative_result

    return TimeResolution(None, 0.0, trimmed, False)


def _try_parse_iso(value: str) -> Optional[datetime]:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=LOCAL_ZONE)
    return parsed.astimezone(LOCAL_ZONE)


def _try_parse_relative(value: str, reference: datetime) -> Optional[TimeResolution]:
    for keyword, offset_days in RELATIVE_KEYWORDS:
        if keyword in value:
            target_date = (reference + timedelta(days=offset_days)).date()
            extracted = _extract_time(value)
            if extracted:
                target_time, confidence = extracted
            else:
                target_time, confidence = time(9, 0), 0.6

            if keyword == "tonight" and not extracted:
                target_time = time(20, 0)
                confidence = 0.7

            localized_dt = datetime.combine(
                target_date,
                target_time,
                tzinfo=LOCAL_ZONE,
            )
            if offset_days == 0 and keyword != "today":
                # Words like tonight still count as relative
                relative_flag = True
            else:
                relative_flag = True
            return TimeResolution(
                iso=localized_dt.isoformat(),
                confidence=min(0.9, confidence),
                source_text=value,
                is_relative=relative_flag,
            )
    return None


def _extract_time(value: str) -> Optional[tuple[time, float]]:
    match = TIME_PATTERN.search(value)
    if not match:
        return None

    hour = int(match.group("hour"))
    minute = int(match.group("minute") or 0)
    ampm = match.group("ampm")

    if ampm:
        ampm = ampm.lower()
        if ampm == "pm" and hour < 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0
    elif hour == 24:
        hour = 0

    hour = max(0, min(hour, 23))
    minute = max(0, min(minute, 59))
    return time(hour, minute), 0.9

