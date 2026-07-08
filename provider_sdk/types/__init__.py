"""类型常量与重载范围定义。"""

from __future__ import annotations

from provider_sdk.types.candidate import ALL_CAPABILITIES

CONFIG_RELOAD_SCOPE_SELF = "self"
CONFIG_RELOAD_SCOPE_GLOBAL = "global"

__all__ = [
    "CONFIG_RELOAD_SCOPE_SELF",
    "CONFIG_RELOAD_SCOPE_GLOBAL",
    "ALL_CAPABILITIES",
]
