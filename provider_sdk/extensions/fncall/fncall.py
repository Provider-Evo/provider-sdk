"""FnCall 插件 mixin — 注册扩展工具协议。"""

from __future__ import annotations

from typing import Callable, Optional

__all__ = ["FncallPluginMixin"]


class FncallPluginMixin:
    """fncall 类型插件可选混入。"""

    _custom_protocol_factory: Optional[Callable[..., object]] = None

    def register_custom_protocol_factory(
        self, factory: Callable[..., object]
    ) -> None:
        """注册 custom 协议工厂，供 echotools 回调。"""
        self._custom_protocol_factory = factory
        try:
            from echotools.fncall.registry import set_custom_protocol_factory

            set_custom_protocol_factory(factory)
        except ImportError:
            pass
