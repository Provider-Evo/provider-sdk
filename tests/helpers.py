"""Shared test helpers."""

from __future__ import annotations


def assert_non_empty(value: str) -> None:
    assert value.strip(), "expected non-empty string"
