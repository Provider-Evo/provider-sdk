"""平台适配器扩展 — 可选插件类型，非 SDK 核心。"""

from provider_sdk.extensions.platform.adapter import PlatformAdapter
from provider_sdk.extensions.platform.bridge import (
    get_platform_adapter,
    has_platform_adapter,
    try_get_platform_adapter,
)
from provider_sdk.types.candidate import ALL_CAPABILITIES, Candidate, make_id

__all__ = [
    "PlatformAdapter",
    "Candidate",
    "make_id",
    "ALL_CAPABILITIES",
    "get_platform_adapter",
    "has_platform_adapter",
    "try_get_platform_adapter",
]
