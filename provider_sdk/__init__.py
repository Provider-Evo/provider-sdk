"""Provider-V2 平台插件 SDK。

插件作者的唯一依赖入口。插件不得导入 ``src.*``，只能通过本 SDK 与 Host 交互。

核心导出：

- :class:`ProviderPlugin` — 插件基类（生命周期 + 配置）
- :class:`PlatformAdapter` — 平台适配器抽象接口
- :class:`PluginContext` — 运行时上下文（日志 / 配置 / HTTP）
- :class:`PluginConfigBase` — 插件配置模型基类
- :class:`Candidate` — 网关候选项
"""

from provider_sdk.config import Field, PluginConfigBase
from provider_sdk.context import PluginContext
from provider_sdk.platform import PlatformAdapter
from provider_sdk.plugin import ProviderPlugin
from provider_sdk.types import (
    CONFIG_RELOAD_SCOPE_GLOBAL,
    CONFIG_RELOAD_SCOPE_SELF,
    ALL_CAPABILITIES,
)
from provider_sdk.types.candidate import Candidate, make_id

__version__ = "0.1.0"

__all__ = [
    "ProviderPlugin",
    "PlatformAdapter",
    "PluginContext",
    "PluginConfigBase",
    "Field",
    "Candidate",
    "make_id",
    "CONFIG_RELOAD_SCOPE_SELF",
    "CONFIG_RELOAD_SCOPE_GLOBAL",
    "ALL_CAPABILITIES",
    "__version__",
]
