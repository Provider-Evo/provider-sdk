"""向后兼容：``provider_sdk.platform`` 已迁至 ``extensions.platform``。"""

from __future__ import annotations

import warnings

from provider_sdk.extensions.platform.adapter import PlatformAdapter, DEFAULT_CONTEXT_LENGTH

warnings.warn(
    "provider_sdk.platform 已弃用，请改用 provider_sdk.extensions.platform",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["PlatformAdapter", "DEFAULT_CONTEXT_LENGTH"]
