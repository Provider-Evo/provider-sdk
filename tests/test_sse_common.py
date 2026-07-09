"""Tests for provider_sdk.extensions.platform.sse_common."""

from __future__ import annotations

import pytest

from provider_sdk.extensions.platform.sse_common import parse_openai_sse_line


class TestParseOpenAiSseLine:
    def test_returns_none_for_empty_string(self) -> None:
        assert parse_openai_sse_line("") is None

    def test_returns_none_for_done_marker(self) -> None:
        assert parse_openai_sse_line("[DONE]") is None

    def test_returns_text_content(self) -> None:
        data = '{"choices":[{"delta":{"content":"hello"}}]}'
        assert parse_openai_sse_line(data) == "hello"

    def test_raises_valueerror_on_error_field(self) -> None:
        data = '{"error":{"message":"rate limited"}}'
        with pytest.raises(ValueError, match="SSE error"):
            parse_openai_sse_line(data)
