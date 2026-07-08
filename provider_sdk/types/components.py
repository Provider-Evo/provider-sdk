"""组件类型与声明数据结构。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

__all__ = [
    "ComponentType",
    "ComponentInfo",
    "RouteComponentInfo",
    "HookComponentInfo",
    "APIComponentInfo",
]


class ComponentType(str, Enum):
    """插件可向 Host 声明的组件类型。"""

    ROUTE = "route"
    HOOK = "hook"
    API = "api"
    PLATFORM = "platform"


@dataclass
class ComponentInfo:
    """组件声明基类。"""

    name: str
    description: str = ""
    type: ComponentType = ComponentType.API
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_declaration(self, *, handler_name: str = "") -> Dict[str, Any]:
        meta = dict(self.metadata)
        if handler_name:
            meta.setdefault("handler_name", handler_name)
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "metadata": meta,
        }


@dataclass
class RouteComponentInfo(ComponentInfo):
    """HTTP 路由组件。"""

    path: str = ""
    methods: List[str] = field(default_factory=lambda: ["GET"])
    type: ComponentType = field(default=ComponentType.ROUTE, init=False)

    def __post_init__(self) -> None:
        self.metadata.setdefault("path", self.path)
        self.metadata.setdefault("methods", list(self.methods))


@dataclass
class HookComponentInfo(ComponentInfo):
    """生命周期 / 请求钩子组件。"""

    hook_point: str = ""
    order: int = 0
    type: ComponentType = field(default=ComponentType.HOOK, init=False)

    def __post_init__(self) -> None:
        self.metadata.setdefault("hook_point", self.hook_point)
        self.metadata.setdefault("order", self.order)


@dataclass
class APIComponentInfo(ComponentInfo):
    """插件对外 API 组件。"""

    public: bool = False
    version: str = "1"
    type: ComponentType = field(default=ComponentType.API, init=False)

    def __post_init__(self) -> None:
        self.metadata.setdefault("public", self.public)
        self.metadata.setdefault("version", self.version)
