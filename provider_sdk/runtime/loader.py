"""Host 侧插件发现与加载。"""

from __future__ import annotations

import importlib.util
import logging
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

import aiohttp

from provider_sdk.context import HostServices, create_plugin_context
from provider_sdk.extensions.platform.adapter import PlatformAdapter
from provider_sdk.extensions.platform.bridge import try_get_platform_adapter
from provider_sdk.plugin import ProviderPlugin, is_provider_plugin
from provider_sdk.types.manifest import PluginManifest, load_manifest_file

__all__ = [
    "LoadedPlugin",
    "PluginLoadError",
    "PluginLoader",
    "discover_plugin_dirs",
]

logger = logging.getLogger("provider_sdk.runtime.loader")

_MANIFEST_NAME = "_manifest.json"
_ENTRY_MODULE = "plugin.py"
_FACTORY_NAME = "create_plugin"


class PluginLoadError(RuntimeError):
    """插件加载失败。"""


@dataclass
class LoadedPlugin:
    """加载成功的插件记录。"""

    manifest: PluginManifest
    plugin: ProviderPlugin
    plugin_dir: Path
    module_name: str
    components: List[Dict[str, Any]]
    adapter: Optional[PlatformAdapter] = None


def discover_plugin_dirs(plugins_root: Path) -> List[Path]:
    """扫描插件根目录，返回包含 manifest 的子目录列表。"""
    root = plugins_root.resolve()
    if not root.is_dir():
        return []

    candidates: List[Path] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith(".") or child.name.startswith("_"):
            continue
        if (child / _MANIFEST_NAME).is_file() and (child / _ENTRY_MODULE).is_file():
            candidates.append(child)
    return candidates


def _topological_sort(manifests: Mapping[str, PluginManifest]) -> List[str]:
    indegree: Dict[str, int] = {pid: 0 for pid in manifests}
    graph: Dict[str, List[str]] = {pid: [] for pid in manifests}

    for pid, manifest in manifests.items():
        for dep in manifest.dependencies:
            if dep not in manifests:
                raise PluginLoadError(f"插件 {pid} 依赖未找到的插件: {dep}")
            graph[dep].append(pid)
            indegree[pid] += 1

    queue = deque(sorted(pid for pid, deg in indegree.items() if deg == 0))
    ordered: List[str] = []
    while queue:
        current = queue.popleft()
        ordered.append(current)
        for nxt in graph[current]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(ordered) != len(manifests):
        raise PluginLoadError("插件依赖存在环")
    return ordered


def _load_entry_module(plugin_dir: Path, plugin_id: str) -> Any:
    module_name = f"provider_plugin_{plugin_id.replace('.', '_').replace('-', '_')}"
    entry = plugin_dir / _ENTRY_MODULE
    spec = importlib.util.spec_from_file_location(module_name, entry)
    if spec is None or spec.loader is None:
        raise PluginLoadError(f"无法加载入口模块: {entry}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class PluginLoader:
    """扫描 ``plugins/`` 目录并加载 SDK 插件。"""

    def __init__(
        self,
        *,
        host_version: str = "",
        plugin_type_filter: str = "",
    ) -> None:
        self._host_version = host_version
        self._plugin_type_filter = plugin_type_filter.strip().lower()
        self._loaded: Dict[str, LoadedPlugin] = {}
        self._failed: Dict[str, str] = {}

    @property
    def loaded_plugins(self) -> Dict[str, LoadedPlugin]:
        return dict(self._loaded)

    @property
    def failed_plugins(self) -> Dict[str, str]:
        return dict(self._failed)

    async def discover_and_load(
        self,
        plugins_root: Path,
        session: aiohttp.ClientSession,
        *,
        get_plugin_config: Optional[Callable[[str], Mapping[str, Any]]] = None,
        get_global_config: Optional[Callable[[], Mapping[str, Any]]] = None,
        whitelist: Optional[Sequence[str]] = None,
        blacklist: Optional[Sequence[str]] = None,
    ) -> List[LoadedPlugin]:
        """发现并加载合法插件。"""
        plugin_dirs = discover_plugin_dirs(plugins_root)
        manifests: Dict[str, PluginManifest] = {}
        dir_by_id: Dict[str, Path] = {}

        for plugin_dir in plugin_dirs:
            try:
                manifest = load_manifest_file(plugin_dir)
            except Exception as exc:
                self._failed[plugin_dir.name] = str(exc)
                logger.error("manifest 解析失败 [%s]: %s", plugin_dir.name, exc)
                continue

            if self._plugin_type_filter and manifest.plugin_type != self._plugin_type_filter:
                continue

            manifests[manifest.id] = manifest
            dir_by_id[manifest.id] = plugin_dir

        wl = set(whitelist) if whitelist else None
        bl = set(blacklist or [])
        ordered_ids = _topological_sort(manifests)

        loaded: List[LoadedPlugin] = []
        for plugin_id in ordered_ids:
            manifest = manifests[plugin_id]
            short_name = plugin_id.rsplit(".", 1)[-1]

            if wl is not None and short_name not in wl and plugin_id not in wl:
                continue
            if short_name in bl or plugin_id in bl:
                continue

            plugin_dir = dir_by_id[plugin_id]
            try:
                record = await self._load_one(
                    plugin_dir,
                    manifest,
                    session,
                    get_plugin_config=get_plugin_config,
                    get_global_config=get_global_config,
                )
            except Exception as exc:
                self._failed[plugin_id] = str(exc)
                logger.error("插件加载失败 [%s]: %s", plugin_id, exc)
                continue

            self._loaded[plugin_id] = record
            loaded.append(record)

        return loaded

    async def _load_one(
        self,
        plugin_dir: Path,
        manifest: PluginManifest,
        session: aiohttp.ClientSession,
        *,
        get_plugin_config: Optional[Callable[[str], Mapping[str, Any]]] = None,
        get_global_config: Optional[Callable[[], Mapping[str, Any]]] = None,
    ) -> LoadedPlugin:
        module = _load_entry_module(plugin_dir, manifest.id)
        factory = getattr(module, _FACTORY_NAME, None)
        if not callable(factory):
            raise PluginLoadError(f"插件 {manifest.id} 缺少 {_FACTORY_NAME}() 工厂函数")

        instance = factory()
        if not is_provider_plugin(instance):
            raise PluginLoadError(f"插件 {manifest.id} 必须返回 ProviderPlugin 实例")

        adapter = try_get_platform_adapter(instance)
        if manifest.plugin_type == "platform" and adapter is None:
            raise PluginLoadError(
                f"platform 类型插件 {manifest.id} 必须提供平台适配器"
            )

        config_lookup = get_plugin_config or (lambda _pid: {})
        services = HostServices(
            session=session,
            plugin_id=manifest.id,
            plugin_dir=str(plugin_dir.resolve()),
            get_plugin_config=lambda: config_lookup(manifest.id),
            get_global_config=get_global_config,
        )
        ctx = create_plugin_context(services)
        instance._set_context(ctx)

        initial_config = config_lookup(manifest.id)
        if isinstance(initial_config, Mapping):
            instance.set_plugin_config(dict(initial_config))

        components = instance.get_components()
        await instance.on_load()

        if adapter is not None:
            await adapter.init(session)

        return LoadedPlugin(
            manifest=manifest,
            plugin=instance,
            plugin_dir=plugin_dir,
            module_name=module.__name__,
            components=components,
            adapter=adapter,
        )

    async def unload_all(self) -> None:
        """卸载全部已加载插件。"""
        for plugin_id, record in list(self._loaded.items()):
            if record.adapter is not None:
                try:
                    await record.adapter.close()
                except Exception as exc:
                    logger.warning("关闭适配器失败 [%s]: %s", plugin_id, exc)
            try:
                await record.plugin.on_unload()
            except Exception as exc:
                logger.warning("on_unload 失败 [%s]: %s", plugin_id, exc)
        self._loaded.clear()
