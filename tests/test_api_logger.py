import logging
from unittest.mock import patch

import pytest

from src.api_logger import ApiLogger


def test_log_call_disabled_emits_single_warning(caplog):
    with patch('src.api_logger.ENABLE_LOGGING', False):
        logger = ApiLogger()

    with caplog.at_level(logging.WARNING, logger="jarvis.api_fallback"):
        logger.log_call(service="openai", action="chat", error="boom")
        logger.log_call(service="openai", action="chat", error="second error")

    warnings = [record for record in caplog.records if record.name == "jarvis.api_fallback"]
    assert len(warnings) == 1
    assert "API logging disabled" in warnings[0].message
    assert logger.last_disabled_error == "second error"


def test_log_call_enabled_skips_fallback_warning(caplog):
    with patch('src.api_logger.ENABLE_LOGGING', True), patch.object(
        ApiLogger, "_configure_logger", autospec=True
    ):
        logger = ApiLogger()

    with caplog.at_level(logging.WARNING, logger="jarvis.api_fallback"):
        logger.log_call(service="openai", action="chat", error="boom")

    warnings = [record for record in caplog.records if record.name == "jarvis.api_fallback"]
    assert warnings == []

