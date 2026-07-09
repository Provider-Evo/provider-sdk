# Provider 插件开发指南

## 定位

**provider-sdk 是通用插件 SDK**，约定包括：

- 独立包，禁止 `import src.*`
- `plugin.py` + `create_plugin()` + `_manifest.json`
- `ProviderPlugin` 生命周期 + `PluginContext`
- 装饰器声明组件

**平台适配器**（`PlatformAdapter`）是可选扩展，放在 `provider_sdk.extensions.platform`，仅供 `plugin_type=platform` 的插件使用。

## 目录结构

```
plugins/<plugin-name>/
  _manifest.json
  plugin.py
  config.toml          # 可选，Host 管理
```

## Manifest

```json
{
  "manifest_version": 1,
  "id": "author.my-plugin",
  "name": "My Plugin",
  "version": "0.1.0",
  "plugin_type": "general",
  "sdk": { "min_version": "0.2.0" },
  "dependencies": []
}
```

## 组件装饰器

| 装饰器 | 用途 |
|--------|------|
| `@Route(path, methods=[...])` | 注册 HTTP 路由 |
| `@Hook(hook_point)` | 注册 Host 扩展点 |
| `@API(name, public=False)` | 声明插件 API |

Runner 加载后调用 `plugin.get_components()` 收集声明。

## 生命周期

```python
async def on_load(self) -> None: ...
async def on_unload(self) -> None: ...
async def on_config_update(self, scope, config_data, version) -> None: ...
```

## 平台扩展（可选）

仅当 `plugin_type` 为 `platform` 时需要：

```python
from provider_sdk import ProviderPlugin
from provider_sdk.extensions.platform import PlatformAdapter, Candidate, make_id

class MyPlatform(ProviderPlugin, PlatformAdapter):
    @property
    def name(self) -> str:
        return "my_platform"
    # init / candidates / complete / close ...
```

## Host 集成

```python
from provider_sdk.runtime import PluginManager

mgr = PluginManager()
await mgr.load_all(Path("plugins"), session)
routes = mgr.get_components("route")
adapters = mgr.get_platform_adapters()  # 仅 platform 插件
```

仅加载平台插件并注册适配器：

```python
from provider_sdk.integrate import load_platform_plugins, register_platform_adapters

loaded = await load_platform_plugins(Path("plugins"), session)
register_platform_adapters(registry, loaded)
```

## 示例

- `examples/hello_plugin/` — 通用插件（Route/Hook/API）
- `examples/echo_platform/` — 平台扩展

```bash
pytest -q
```
