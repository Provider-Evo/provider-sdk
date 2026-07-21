"""组件声明装饰器 — Route / Hook / API。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from provider_sdk.types.components import (
    APIComponentInfo,
    ComponentInfo,
    HookComponentInfo,
    RouteComponentInfo,
)

__all__ = ["Route", "Hook", "API", "collect_components"]

_COMPONENT_INFO_ATTR = "__provider_component_info__"
_Decorator = Callable[[Callable[..., Any]], Callable[..., Any]]


def _attach_info(func: Callable[..., Any], info: ComponentInfo) -> Callable[..., Any]:
    setattr(func, _COMPONENT_INFO_ATTR, info)
    return func


def Route(
    path: str,
    *,
    methods: list[str] | None = None,
    name: str = "",
    description: str = "",
) -> _Decorator:
    """声明 Web / API 路由处理器。"""

    normalized_methods = [m.upper() for m in (methods or ["GET"])]
    route_name = name or path.strip("/").replace("/", "_") or "route"

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        info = RouteComponentInfo(
            name=route_name,
            description=description or f"Route {path}",
            path=path,
            methods=normalized_methods,
        )
        return _attach_info(func, info)

    return decorator


def Hook(
    hook_point: str,
    *,
    name: str = "",
    description: str = "",
    order: int = 0,
) -> _Decorator:
    """声明 Host 扩展点钩子。"""

    hook_name = name or hook_point

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        info = HookComponentInfo(
            name=hook_name,
            description=description or f"Hook {hook_point}",
            hook_point=hook_point,
            order=order,
        )
        return _attach_info(func, info)

    return decorator


def API(
    name: str,
    *,
    description: str = "",
    public: bool = False,
    version: str = "1",
) -> _Decorator:
    """声明可供 Host 或其他插件调用的 API。"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        info = APIComponentInfo(
            name=name,
            description=description or f"API {name}",
            public=public,
            version=version,
        )
        return _attach_info(func, info)

    return decorator


def collect_components(instance: object) -> list[dict[str, Any]]:
    """从插件实例收集全部装饰器声明的组件。"""
    components: list[dict[str, Any]] = []
    for attr_name in dir(instance):
        if attr_name.startswith("_"):
            continue
        try:
            attr = getattr(instance, attr_name)
        except Exception:
            continue
        if not callable(attr):
            continue
        info = getattr(attr, _COMPONENT_INFO_ATTR, None)
        if isinstance(info, ComponentInfo):
            components.append(info.to_declaration(handler_name=attr_name))
    return components
