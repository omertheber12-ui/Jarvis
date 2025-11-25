"""Tests for time utility helpers."""

from datetime import datetime

from src.time_utils import (
    LOCAL_ZONE,
    format_human,
    is_late_hour,
    now_local,
    resolve_time_reference,
)


def test_format_human_includes_expected_components():
    sample = datetime(2025, 11, 25, 15, 45, tzinfo=LOCAL_ZONE)
    human = format_human(sample)
    assert "November" in human
    assert "2025" in human
    assert "15:45" in human


def test_is_late_hour_threshold():
    early = datetime(2025, 11, 25, 18, 0, tzinfo=LOCAL_ZONE)
    late = datetime(2025, 11, 25, 22, 30, tzinfo=LOCAL_ZONE)
    assert is_late_hour(early) is False
    assert is_late_hour(late) is True


def test_resolve_time_reference_iso():
    result = resolve_time_reference("2025-11-25T09:30:00+02:00")
    assert result.iso.startswith("2025-11-25T07") or result.iso.startswith(
        "2025-11-25T09"
    )  # allow for timezone adjustments
    assert result.confidence == 1.0


def test_resolve_time_reference_relative_with_time():
    reference = datetime(2025, 11, 25, 10, 0, tzinfo=LOCAL_ZONE)
    result = resolve_time_reference("Tomorrow at 3 pm", reference)
    assert result.iso.startswith("2025-11-26T15:00")
    assert 0.0 < result.confidence < 1.0


def test_resolve_time_reference_unknown():
    result = resolve_time_reference("someday maybe")
    assert result.iso is None
    assert result.confidence == 0.0

