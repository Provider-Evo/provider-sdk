"""能力代理：配置、HTTP、日志。"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Optional

import aiohttp

__all__ = ["ConfigCapability", "HttpCapability", "LoggingCapability"]

GetConfigFn = Callable[[str, str], Any]
GetGlobalConfigFn = Callable[[], Mapping[str, Any]]


class LoggingCapability:
    """插件日志能力。"""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    @property
    def logger(self) -> logging.Logger:
        return self._logger


class ConfigCapability:
    """插件配置读取能力。"""

    def __init__(
        self,
        *,
        get_plugin_config: Callable[[], Mapping[str, Any]],
        get_global_config: Optional[GetGlobalConfigFn] = None,
    ) -> None:
        self._get_plugin_config = get_plugin_config
        self._get_global_config = get_global_config

    def get_plugin(self) -> dict[str, Any]:
        """返回当前插件配置字典副本。"""
        raw = self._get_plugin_config()
        return dict(raw) if isinstance(raw, Mapping) else {}

    def get_global(self) -> dict[str, Any]:
        """返回 Host 全局配置字典副本。"""
        if self._get_global_config is None:
            return {}
        raw = self._get_global_config()
        return dict(raw) if isinstance(raw, Mapping) else {}

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """读取全局配置中的嵌套键。"""
        data = self.get_global()
        node = data.get(section)
        if isinstance(node, Mapping):
            return node.get(key, default)
        return default


class HttpCapability:
    """共享 HTTP 会话能力。"""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    @property
    def session(self) -> aiohttp.ClientSession:
        return self._session

    async def request(self, method: str, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        """对共享会话发起请求。"""
        return await self._session.request(method, url, **kwargs)
