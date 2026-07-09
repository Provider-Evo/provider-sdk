"""Provider 插件 SDK — 通用插件开发包。

插件作者的唯一依赖入口。插件不得导入 ``src.*``，只能通过本 SDK 与 Host 交互。

核心导出：

- :class:`ProviderPlugin` — 插件基类（生命周期 + 配置 + 组件收集）
- :class:`PluginContext` — 运行时上下文
- :func:`Route` / :func:`Hook` / :func:`API` — 组件声明装饰器
- :class:`PluginConfigBase` — 配置模型

平台适配器为**可选扩展**：``provider_sdk.extensions.platform``
"""

from provider_sdk.components import API, Hook, Route, collect_components
from provider_sdk.config import Field, PluginConfigBase
from provider_sdk.context import PluginContext
from provider_sdk.plugin import ProviderPlugin, is_provider_plugin
from provider_sdk.types import (
    CONFIG_RELOAD_SCOPE_GLOBAL,
    CONFIG_RELOAD_SCOPE_SELF,
)

__version__ = "0.3.0"

__all__ = [
    "ProviderPlugin",
    "is_provider_plugin",
    "PluginContext",
    "PluginConfigBase",
    "Field",
    "Route",
    "Hook",
    "API",
    "collect_components",
    "CONFIG_RELOAD_SCOPE_SELF",
    "CONFIG_RELOAD_SCOPE_GLOBAL",
    "__version__",
]
