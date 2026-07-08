"""插件 manifest 解析与校验。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

__all__ = ["PluginManifest", "parse_manifest", "load_manifest_file"]

_MANIFEST_FILENAME = "_manifest.json"
_PLUGIN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,126}[a-z0-9]$")


@dataclass(frozen=True)
class PluginManifest:
    """``_manifest.json`` 强类型视图。"""

    id: str
    name: str
    version: str
    description: str = ""
    plugin_type: str = "general"
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    host_min_version: str = ""
    host_max_version: str = ""
    sdk_min_version: str = "0.1.0"
    sdk_max_version: str = "0.99.99"
    manifest_version: int = 1
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def plugin_dependency_ids(self) -> List[str]:
        """依赖插件 ID 列表（``dependencies`` 字段别名）。"""
        return list(self.dependencies)


def _read_author(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, Mapping):
        return str(value.get("name") or "").strip()
    return ""


def _read_dependencies(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
        elif isinstance(item, Mapping):
            dep_id = str(item.get("id") or item.get("plugin_id") or "").strip()
            if dep_id:
                out.append(dep_id)
    return out


def parse_manifest(data: Mapping[str, Any]) -> PluginManifest:
    """将原始 JSON 映射解析为 :class:`PluginManifest`。

    Raises:
        ValueError: manifest 缺少必填字段或格式非法。
    """
    plugin_id = str(data.get("id") or "").strip()
    if not plugin_id:
        raise ValueError("manifest 缺少 id")
    if not _PLUGIN_ID_RE.match(plugin_id):
        raise ValueError(f"manifest id 格式非法: {plugin_id}")

    name = str(data.get("name") or plugin_id).strip()
    version = str(data.get("version") or "0.0.0").strip()
    host_app = data.get("host_application") if isinstance(data.get("host_application"), Mapping) else {}
    sdk_info = data.get("sdk") if isinstance(data.get("sdk"), Mapping) else {}

    return PluginManifest(
        id=plugin_id,
        name=name,
        version=version,
        description=str(data.get("description") or "").strip(),
        plugin_type=str(data.get("plugin_type") or "platform").strip().lower(),
        author=_read_author(data.get("author")),
        dependencies=_read_dependencies(data.get("dependencies")),
        capabilities=[str(x).strip() for x in (data.get("capabilities") or []) if str(x).strip()],
        host_min_version=str(host_app.get("min_version") or "").strip(),
        host_max_version=str(host_app.get("max_version") or "").strip(),
        sdk_min_version=str(sdk_info.get("min_version") or "0.1.0").strip(),
        sdk_max_version=str(sdk_info.get("max_version") or "0.99.99").strip(),
        manifest_version=int(data.get("manifest_version") or 1),
        raw=dict(data),
    )


def load_manifest_file(plugin_dir: Path) -> PluginManifest:
    """从插件目录读取 ``_manifest.json``。"""
    path = plugin_dir / _MANIFEST_FILENAME
    if not path.is_file():
        raise FileNotFoundError(f"缺少 {_MANIFEST_FILENAME}: {plugin_dir}")
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, Mapping):
        raise ValueError(f"manifest 根节点必须是对象: {path}")
    return parse_manifest(data)
