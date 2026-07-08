"""Provider 通用插件基类。"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, ClassVar, Iterable

from provider_sdk.components import collect_components
from provider_sdk.config import (
    PluginConfigBase,
    build_plugin_default_config,
    is_plugin_config_class,
    merge_plugin_config_data,
    validate_plugin_config,
)
from provider_sdk.context import PluginContext
from provider_sdk.types import CONFIG_RELOAD_SCOPE_SELF

__all__ = ["ProviderPlugin", "is_provider_plugin"]


class ProviderPlugin:
    """SDK 插件基类 — 对标 maibot-sdk 的 ``MaiBotPlugin``。

    通用插件通过 ``@Route`` / ``@Hook`` / ``@API`` 向 Host 声明能力。
    平台适配器是**可选扩展**，见 ``provider_sdk.extensions.platform``。

    用法示例::

        from provider_sdk import ProviderPlugin, Route, Hook

        class HelloPlugin(ProviderPlugin):
            async def on_load(self) -> None:
                self.ctx.logger.info("hello")

            @Route("/plugins/hello", methods=["GET"])
            async def hello(self) -> dict:
                return {"ok": True}

        def create_plugin() -> HelloPlugin:
            return HelloPlugin()
    """

    config_reload_subscriptions: ClassVar[Iterable[str]] = ()
    config_model: ClassVar[type[PluginConfigBase] | None] = None

    def __init__(self) -> None:
        self._ctx: PluginContext | None = None
        self._plugin_config_data: dict[str, Any] = {}
        self._plugin_config_instance: PluginConfigBase | None = None

    @classmethod
    def get_config_model(cls) -> type[PluginConfigBase] | None:
        candidate = cls.config_model
        return candidate if is_plugin_config_class(candidate) else None

    @classmethod
    def has_config_model(cls) -> bool:
        return cls.get_config_model() is not None

    @classmethod
    def build_default_config(cls) -> dict[str, Any]:
        config_class = cls.get_config_model()
        if config_class is None:
            return {}
        return build_plugin_default_config(config_class)

    def normalize_plugin_config(
        self,
        config_data: Mapping[str, Any] | None,
    ) -> tuple[dict[str, Any], bool]:
        raw_config: dict[str, Any] = dict(config_data) if isinstance(config_data, Mapping) else {}
        config_class = type(self).get_config_model()
        if config_class is None:
            return raw_config, False

        default_config = type(self).build_default_config()
        if not raw_config:
            validated = validate_plugin_config(config_class, default_config)
            return validated.model_dump(mode="python"), bool(default_config)

        merged, changed = merge_plugin_config_data(default_config, raw_config)
        validated = validate_plugin_config(config_class, merged)
        normalized = validated.model_dump(mode="python")
        return normalized, changed or normalized != merged

    def set_plugin_config(self, config: dict[str, Any]) -> None:
        normalized, _ = self.normalize_plugin_config(config)
        self._plugin_config_data = normalized

        config_class = type(self).get_config_model()
        if config_class is None:
            self._plugin_config_instance = None
            return

        try:
            self._plugin_config_instance = validate_plugin_config(config_class, normalized)
        except Exception as exc:
            self._plugin_config_instance = None
            self._get_logger().warning("插件配置校验失败: %s", exc)

    @property
    def config(self) -> PluginConfigBase:
        if not type(self).has_config_model():
            raise RuntimeError("当前插件未声明 config_model")
        if self._plugin_config_instance is None:
            raise RuntimeError("当前插件配置尚未注入")
        return self._plugin_config_instance

    def get_plugin_config_data(self) -> dict[str, Any]:
        return dict(self._plugin_config_data)

    @property
    def ctx(self) -> PluginContext:
        if self._ctx is None:
            raise RuntimeError("插件上下文尚未初始化")
        return self._ctx

    def _set_context(self, ctx: PluginContext) -> None:
        self._ctx = ctx

    def _get_logger(self) -> logging.Logger:
        if self._ctx is not None:
            return self._ctx.logger
        return logging.getLogger("provider_sdk.plugin")

    def get_components(self) -> list[dict[str, Any]]:
        """收集装饰器声明的组件 — Runner 加载后自动调用。"""
        return collect_components(self)

    async def on_load(self) -> None:
        """插件加载完成。"""

    async def on_unload(self) -> None:
        """插件卸载前。"""

    async def on_config_update(
        self,
        scope: str,
        config_data: dict[str, object],
        version: str,
    ) -> None:
        if scope == CONFIG_RELOAD_SCOPE_SELF:
            self.set_plugin_config(dict(config_data))
        del version


def is_provider_plugin(instance: Any) -> bool:
    """判断对象是否为合法 Provider 插件。"""
    return isinstance(instance, ProviderPlugin)
