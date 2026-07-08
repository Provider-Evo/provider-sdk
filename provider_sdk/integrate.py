"""与 Provider Host 集成的辅助函数。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

import aiohttp

from provider_sdk.runtime.loader import LoadedPlugin, PluginLoader
from provider_sdk.runtime.manager import PluginManager

__all__ = [
    "load_plugins",
    "load_platform_plugins",
    "register_platform_adapters",
]


async def load_plugins(
    plugins_root: Path,
    session: aiohttp.ClientSession,
    *,
    host_version: str = "",
    plugin_type_filter: str = "",
    get_plugin_config: Optional[Callable[[str], Mapping[str, Any]]] = None,
    get_global_config: Optional[Callable[[], Mapping[str, Any]]] = None,
    whitelist: Optional[Sequence[str]] = None,
    blacklist: Optional[Sequence[str]] = None,
) -> list[LoadedPlugin]:
    """加载 ``plugins/`` 目录下的插件（默认不过滤类型）。"""
    loader = PluginLoader(host_version=host_version, plugin_type_filter=plugin_type_filter)
    return await loader.discover_and_load(
        plugins_root,
        session,
        get_plugin_config=get_plugin_config,
        get_global_config=get_global_config,
        whitelist=whitelist,
        blacklist=blacklist,
    )


async def load_platform_plugins(
    plugins_root: Path,
    session: aiohttp.ClientSession,
    **kwargs: Any,
) -> list[LoadedPlugin]:
    """仅加载 ``plugin_type=platform`` 的插件。"""
    return await load_plugins(
        plugins_root,
        session,
        plugin_type_filter="platform",
        **kwargs,
    )


def register_platform_adapters(registry: Any, loaded: Sequence[LoadedPlugin]) -> None:
    """将已加载插件中的平台适配器注册到 Host Registry。"""
    for record in loaded:
        if record.adapter is None:
            continue
        adapter = record.adapter
        if hasattr(registry, "register") and callable(registry.register):
            registry.register(adapter)
            continue
        inner = getattr(registry, "_registry", None)
        if inner is not None and hasattr(inner, "register"):
            inner.register(adapter)
            continue
        raise TypeError("registry 不支持 register(adapter)")
