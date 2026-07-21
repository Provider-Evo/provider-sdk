"""配置模型测试。"""

from provider_sdk import Field, PluginConfigBase, ProviderPlugin
from provider_sdk.core.config import build_plugin_default_config, merge_plugin_config_data


class DemoConfig(PluginConfigBase):
    enabled: bool = Field(default=True)
    endpoint: str = Field(default="http://127.0.0.1:11434")


class DemoPlugin(ProviderPlugin):
    config_model = DemoConfig


def test_default_config() -> None:
    data = build_plugin_default_config(DemoConfig)
    assert data["enabled"] is True
    assert data["endpoint"].startswith("http")


def test_merge_config() -> None:
    merged, changed = merge_plugin_config_data(
        {"enabled": True, "endpoint": "http://a"},
        {"endpoint": "http://b"},
    )
    assert changed is True
    assert merged["endpoint"] == "http://b"


def test_plugin_normalize_config() -> None:
    plugin = DemoPlugin()
    normalized, changed = plugin.normalize_plugin_config({"endpoint": "http://c"})
    assert normalized["enabled"] is True
    assert normalized["endpoint"] == "http://c"
    assert changed is True
