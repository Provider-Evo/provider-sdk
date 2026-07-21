"""Host 侧插件发现与加载。"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

import aiohttp

from provider_sdk.core.context import HostServices, create_plugin_context
from provider_sdk.extensions.platform.adapter import PlatformAdapter
from provider_sdk.extensions.platform.bridge import try_get_platform_adapter
from provider_sdk.core.plugin import ProviderPlugin, is_provider_plugin
from provider_sdk.types.manifest import (
    PluginManifest,
    load_manifest_file,
    resolve_manifest_path,
)

__all__ = [
    "LoadedPlugin",
    "PluginLoadError",
    "PluginLoader",
    "discover_plugin_dirs",
    "purge_plugin_modules",
]

logger = logging.getLogger("provider_sdk.runtime.loader")

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
        try:
            resolve_manifest_path(child)
        except FileNotFoundError:
            continue
        if (child / _ENTRY_MODULE).is_file():
            candidates.append(child)
    return candidates


def _topological_sort(
    manifests: Mapping[str, PluginManifest],
    failed: Optional[Dict[str, str]] = None,
) -> List[str]:
    """拓扑排序，容错处理缺失依赖和循环依赖。"""
    valid_ids = _filter_valid_ids(manifests, failed)
    indegree, graph = _build_graph(valid_ids, manifests)
    queue = deque(sorted(pid for pid, deg in indegree.items() if deg == 0))
    ordered: List[str] = []
    while queue:
        current = queue.popleft()
        ordered.append(current)
        for nxt in graph[current]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    _mark_cycles(valid_ids, ordered, failed)
    return ordered


def _synthetic_module_name(plugin_id: str) -> str:
    return f"provider_plugin_{plugin_id.replace('.', '_').replace('-', '_')}"


def purge_plugin_modules(plugin_id: str, plugin_dir: Path) -> List[str]:
    """清理插件目录下已导入的模块缓存（热重载前必须调用）。"""
    removed: List[str] = []
    plugin_path = plugin_dir.resolve()
    synthetic = _synthetic_module_name(plugin_id)

    for module_name, module in list(sys.modules.items()):
        if module_name == synthetic:
            removed.append(module_name)
            sys.modules.pop(module_name, None)
            continue

        module_file = getattr(module, "__file__", None)
        if module_file is None:
            continue
        try:
            module_path = Path(module_file).resolve()
        except Exception:
            continue
        if module_path.is_relative_to(plugin_path):
            removed.append(module_name)
            sys.modules.pop(module_name, None)

    importlib.invalidate_caches()
    return removed


def _load_entry_module(plugin_dir: Path, plugin_id: str) -> Any:
    root = str(plugin_dir.resolve())
    if root not in sys.path:
        sys.path.insert(0, root)
    module_name = _synthetic_module_name(plugin_id)
    entry = plugin_dir / _ENTRY_MODULE
    spec = importlib.util.spec_from_file_location(module_name, entry)
    if spec is None or spec.loader is None:
        raise PluginLoadError(f"无法加载入口模块: {entry}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module



def _collect_manifests(
    plugin_dirs: list[Path],
    *,
    plugin_type_filter: str,
    failed: dict[str, str],
) -> tuple[dict[str, "PluginManifest"], dict[str, Path]]:
    manifests: dict[str, PluginManifest] = {}
    dir_by_id: dict[str, Path] = {}
    for plugin_dir in plugin_dirs:
        try:
            manifest = load_manifest_file(plugin_dir)
        except Exception as exc:
            failed[plugin_dir.name] = str(exc)
            logger.error("manifest 解析失败 [%s]: %s", plugin_dir.name, exc)
            continue
        if plugin_type_filter and manifest.plugin_type != plugin_type_filter:
            continue
        manifests[manifest.id] = manifest
        dir_by_id[manifest.id] = plugin_dir
    return manifests, dir_by_id


def _should_skip_plugin(
    plugin_id: str,
    *,
    whitelist: set[str] | None,
    blacklist: set[str],
) -> bool:
    short_name = plugin_id.rsplit(".", 1)[-1]
    if whitelist is not None and short_name not in whitelist and plugin_id not in whitelist:
        return True
    return short_name in blacklist or plugin_id in blacklist


def _filter_valid_ids(
    manifests: dict[str, "PluginManifest"],
    failed: dict[str, str] | None,
) -> set[str]:
    valid_ids = set(manifests.keys())
    skipped: list[str] = []
    for pid, manifest in manifests.items():
        for dep in manifest.dependencies:
            if dep not in manifests:
                skipped.append(pid)
                if failed is not None:
                    failed[pid] = f"依赖未找到: {dep}"
                logger.error("插件 %s 依赖未找到的插件: %s，跳过", pid, dep)
                break
    for pid in skipped:
        valid_ids.discard(pid)
    return valid_ids


def _build_graph(valid_ids: set[str], manifests: dict[str, "PluginManifest"]) -> tuple[dict[str, int], dict[str, list[str]]]:
    indegree: dict[str, int] = {pid: 0 for pid in valid_ids}
    graph: dict[str, list[str]] = {pid: [] for pid in valid_ids}
    for pid in valid_ids:
        for dep in manifests[pid].dependencies:
            if dep in valid_ids:
                graph[dep].append(pid)
                indegree[pid] += 1
    return indegree, graph


def _mark_cycles(valid_ids: set[str], ordered: list[str], failed: dict[str, str] | None) -> None:
    remaining = valid_ids - set(ordered)
    for pid in remaining:
        if failed is not None:
            failed[pid] = "插件依赖存在循环"
        logger.error("插件 %s 依赖存在循环，跳过", pid)



def _instantiate_plugin(module: Any, plugin_id: str) -> ProviderPlugin:
    factory = getattr(module, _FACTORY_NAME, None)
    if not callable(factory):
        raise PluginLoadError(f"插件 {plugin_id} 缺少 {_FACTORY_NAME}() 工厂函数")
    instance = factory()
    if not is_provider_plugin(instance):
        raise PluginLoadError(f"插件 {plugin_id} 必须返回 ProviderPlugin 实例")
    return instance


async def _bind_plugin_context(
    instance: ProviderPlugin,
    manifest: PluginManifest,
    plugin_dir: Path,
    session: aiohttp.ClientSession,
    *,
    get_plugin_config: Optional[Callable[[str], Mapping[str, Any]]] = None,
    get_global_config: Optional[Callable[[], Mapping[str, Any]]] = None,
) -> None:
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


async def _init_platform_adapter(
    instance: ProviderPlugin,
    manifest: PluginManifest,
    session: aiohttp.ClientSession,
) -> Optional[PlatformAdapter]:
    adapter = try_get_platform_adapter(instance)
    if manifest.plugin_type == "platform" and adapter is None:
        raise PluginLoadError(
            f"platform 类型插件 {manifest.id} 必须提供平台适配器（get_adapter 或 _adapter）"
        )
    if adapter is not None and not getattr(instance, "_adapter_inited", False):
        await adapter.init(session)
        instance._adapter_inited = True  # type: ignore[attr-defined]
    return adapter


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
        plugin_dirs = discover_plugin_dirs(plugins_root)
        manifests, dir_by_id = _collect_manifests(
            plugin_dirs,
            plugin_type_filter=self._plugin_type_filter,
            failed=self._failed,
        )
        wl = set(whitelist) if whitelist else None
        bl = set(blacklist or [])
        loaded: List[LoadedPlugin] = []
        for plugin_id in _topological_sort(manifests, failed=self._failed):
            if _should_skip_plugin(plugin_id, whitelist=wl, blacklist=bl):
                continue
            plugin_dir = dir_by_id[plugin_id]
            try:
                record = await self._load_one(
                    plugin_dir,
                    manifests[plugin_id],
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
        instance = _instantiate_plugin(module, manifest.id)
        await _bind_plugin_context(
            instance,
            manifest,
            plugin_dir,
            session,
            get_plugin_config=get_plugin_config,
            get_global_config=get_global_config,
        )
        components = instance.get_components()
        await instance.on_load()
        adapter = await _init_platform_adapter(instance, manifest, session)
        return LoadedPlugin(
            manifest=manifest,
            plugin=instance,
            plugin_dir=plugin_dir,
            module_name=module.__name__,
            components=components,
            adapter=adapter,
        )

    def purge_plugin_modules(self, plugin_id: str, plugin_dir: Path) -> List[str]:
        """清理指定插件的模块缓存。"""
        return purge_plugin_modules(plugin_id, plugin_dir)

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
            try:
                self.purge_plugin_modules(plugin_id, record.plugin_dir)
            except Exception as exc:
                logger.warning("清理插件模块缓存失败 [%s]: %s", plugin_id, exc)
        self._loaded.clear()
