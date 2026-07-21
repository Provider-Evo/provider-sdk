"""插件运行时上下文。"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Optional

import aiohttp

from provider_sdk.types.caps import ConfigCapability, HttpCapability, LoggingCapability

__all__ = ["HostServices", "PluginContext", "create_plugin_context"]


@dataclass
class HostServices:
    """Host 注入给 SDK 的运行时服务集合。"""

    session: aiohttp.ClientSession
    plugin_id: str
    plugin_dir: str = ""
    get_plugin_config: Any = None
    get_global_config: Any = None
    logger: Optional[logging.Logger] = None


class PluginContext:
    """插件运行时上下文。

    插件通过 ``self.ctx`` 访问日志、配置与 HTTP 会话。
    """

    def __init__(
        self,
        *,
        plugin_id: str,
        plugin_dir: str,
        logger: logging.Logger,
        config: ConfigCapability,
        http: HttpCapability,
    ) -> None:
        self.plugin_id = plugin_id
        self.plugin_dir = plugin_dir
        self.logger = logger
        self.config = config
        self.http = http

    @property
    def paths(self) -> Mapping[str, str]:
        """插件相关路径。"""
        return {"plugin_dir": self.plugin_dir}


def create_plugin_context(services: HostServices) -> PluginContext:
    """根据 Host 服务构造插件上下文。"""
    plugin_id = services.plugin_id
    logger = services.logger or logging.getLogger(f"provider_sdk.plugin.{plugin_id}")

    def _plugin_config() -> Mapping[str, Any]:
        if callable(services.get_plugin_config):
            raw = services.get_plugin_config()
            return dict(raw) if isinstance(raw, Mapping) else {}
        return {}

    config_cap = ConfigCapability(
        get_plugin_config=_plugin_config,
        get_global_config=services.get_global_config if callable(services.get_global_config) else None,
    )
    http_cap = HttpCapability(services.session)
    return PluginContext(
        plugin_id=plugin_id,
        plugin_dir=services.plugin_dir,
        logger=logger,
        config=config_cap,
        http=http_cap,
    )
