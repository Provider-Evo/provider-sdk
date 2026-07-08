"""Host 侧插件运行时管理器。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

import aiohttp

from provider_sdk.extensions.platform.adapter import PlatformAdapter
from provider_sdk.runtime.loader import LoadedPlugin, PluginLoader

__all__ = ["PluginManager"]


class PluginManager:
    """已加载插件的统一管理入口。"""

    def __init__(self, *, host_version: str = "") -> None:
        self._host_version = host_version
        self._loader = PluginLoader(host_version=host_version, plugin_type_filter="")
        self._records: Dict[str, LoadedPlugin] = {}

    @property
    def loader(self) -> PluginLoader:
        return self._loader

    @property
    def plugins(self) -> Dict[str, LoadedPlugin]:
        return dict(self._records)

    async def load_all(
        self,
        plugins_root: Path,
        session: aiohttp.ClientSession,
        *,
        get_plugin_config: Optional[Callable[[str], Mapping[str, Any]]] = None,
        get_global_config: Optional[Callable[[], Mapping[str, Any]]] = None,
        whitelist: Optional[Sequence[str]] = None,
        blacklist: Optional[Sequence[str]] = None,
    ) -> List[LoadedPlugin]:
        loaded = await self._loader.discover_and_load(
            plugins_root,
            session,
            get_plugin_config=get_plugin_config,
            get_global_config=get_global_config,
            whitelist=whitelist,
            blacklist=blacklist,
        )
        for record in loaded:
            self._records[record.manifest.id] = record
        return loaded

    async def unload_all(self) -> None:
        await self._loader.unload_all()
        self._records.clear()

    def get_components(self, component_type: str | None = None) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for record in self._records.values():
            for comp in record.components:
                if component_type is None or comp.get("type") == component_type:
                    item = dict(comp)
                    item["plugin_id"] = record.manifest.id
                    out.append(item)
        return out

    def get_platform_adapters(self) -> List[PlatformAdapter]:
        return [r.adapter for r in self._records.values() if r.adapter is not None]

    def get_by_id(self, plugin_id: str) -> Optional[LoadedPlugin]:
        return self._records.get(plugin_id)
