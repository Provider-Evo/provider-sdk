"""Shared SSE parser for OpenAI-compatible streaming APIs."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional, Union

__all__ = ["load_sse_json", "parse_openai_sse_line"]


def load_sse_json(data_str: str) -> Optional[Dict[str, Any]]:
    if not data_str or data_str == "[DONE]":
        return None
    try:
        obj = json.loads(data_str)
    except (json.JSONDecodeError, ValueError):
        return None
    if "error" in obj:
        raise ValueError("SSE error: {}".format(obj["error"]))
    return obj


def parse_openai_sse_line(data_str: str) -> Optional[Union[str, Dict[str, Any]]]:
    obj = load_sse_json(data_str)
    if obj is None:
        return None
    choices = obj.get("choices", [])
    if not choices:
        usage = obj.get("usage")
        if usage:
            return {"usage": usage}
        return None
    choice = choices[0]
    delta = choice.get("delta", {})
    reasoning_content = delta.get("reasoning_content")
    if reasoning_content:
        return {"thinking": reasoning_content}
    content = delta.get("content")
    if content:
        return content
    usage = obj.get("usage")
    if usage:
        return {"usage": usage}
    return None
