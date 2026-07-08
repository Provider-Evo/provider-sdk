"""与 Provider Host 注册表集成的辅助函数。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

import aiohttp

from provider_sdk.runtime.loader import LoadedPlugin, PluginLoader

__all__ = ["load_platform_plugins", "register_loaded_plugins"]


async def load_platform_plugins(
    plugins_root: Path,
    session: aiohttp.ClientSession,
    *,
    host_version: str = "",
    get_plugin_config: Optional[Callable[[str], Mapping[str, Any]]] = None,
    get_global_config: Optional[Callable[[], Mapping[str, Any]]] = None,
    whitelist: Optional[Sequence[str]] = None,
    blacklist: Optional[Sequence[str]] = None,
) -> list[LoadedPlugin]:
    """发现并加载 ``plugins/`` 目录下的平台插件。"""
    loader = PluginLoader(host_version=host_version, plugin_type_filter="platform")
    return await loader.discover_and_load(
        plugins_root,
        session,
        get_plugin_config=get_plugin_config,
        get_global_config=get_global_config,
        whitelist=whitelist,
        blacklist=blacklist,
    )


def register_loaded_plugins(registry: Any, loaded: Sequence[LoadedPlugin]) -> None:
    """将已加载插件的适配器注册到 echotools 风格注册表。

    ``registry`` 需实现 ``register(adapter)`` 或内部 ``_registry.register``。
    """
    for record in loaded:
        adapter = record.adapter
        if hasattr(registry, "register") and callable(registry.register):
            registry.register(adapter)
            continue
        inner = getattr(registry, "_registry", None)
        if inner is not None and hasattr(inner, "register"):
            inner.register(adapter)
            continue
        raise TypeError("registry 不支持 register(adapter)")
