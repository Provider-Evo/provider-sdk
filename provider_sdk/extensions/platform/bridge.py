"""平台适配器提取辅助 — 仅 platform 类型插件需要。"""

from __future__ import annotations

from typing import Any, Optional

from provider_sdk.extensions.platform.adapter import PlatformAdapter
from provider_sdk.plugin import ProviderPlugin

__all__ = [
    "get_platform_adapter",
    "has_platform_adapter",
    "try_get_platform_adapter",
]


def has_platform_adapter(plugin: ProviderPlugin) -> bool:
    """判断插件是否提供平台适配器。"""
    return try_get_platform_adapter(plugin) is not None


def try_get_platform_adapter(plugin: ProviderPlugin) -> Optional[PlatformAdapter]:
    """尝试提取平台适配器，不存在时返回 ``None``。"""
    if isinstance(plugin, PlatformAdapter):
        return plugin

    getter = getattr(plugin, "get_adapter", None)
    if callable(getter):
        adapter = getter()
        if isinstance(adapter, PlatformAdapter):
            return adapter
    return None


def get_platform_adapter(plugin: ProviderPlugin) -> PlatformAdapter:
    """提取平台适配器，不存在时抛出 ``TypeError``。"""
    adapter = try_get_platform_adapter(plugin)
    if adapter is None:
        raise TypeError(
            f"插件 {type(plugin).__name__} 未提供平台适配器；"
            "请继承 extensions.platform.PlatformAdapter 或实现 get_adapter()"
        )
    return adapter
