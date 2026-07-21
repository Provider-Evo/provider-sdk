"""Provider 插件 SDK — 通用插件开发包。"""

from provider_sdk.core.components import API, Hook, Route, collect_components
from provider_sdk.core.config import Field, PluginConfigBase
from provider_sdk.core.context import PluginContext
from provider_sdk.core.plugin import ProviderPlugin, is_provider_plugin
from provider_sdk.types import CONFIG_RELOAD_SCOPE_GLOBAL, CONFIG_RELOAD_SCOPE_SELF
from provider_sdk.types.model_ids import ModelIdRegistry, upstream_to_public_id

__version__ = "0.3.5"

__all__ = [
    "ProviderPlugin", "is_provider_plugin", "PluginContext",
    "PluginConfigBase", "Field", "Route", "Hook", "API", "collect_components",
    "CONFIG_RELOAD_SCOPE_SELF", "CONFIG_RELOAD_SCOPE_GLOBAL",
    "ModelIdRegistry", "upstream_to_public_id", "__version__",
]
