# provider-sdk

Provider-V2 **通用插件 SDK**，对标 [maibot-plugin-sdk](https://github.com/Mai-with-u/maibot-plugin-sdk)。

平台适配器只是可选扩展（`extensions.platform`），不是 SDK 核心。

## 安装

```bash
pip install provider-sdk
```

## 快速开始

```
plugins/
  my_plugin/
    _manifest.json
    plugin.py
```

```python
from provider_sdk import ProviderPlugin, Route, Hook, API

class MyPlugin(ProviderPlugin):
    async def on_load(self) -> None:
        self.ctx.logger.info("loaded")

    @Route("/plugins/my/status", methods=["GET"])
    async def status(self) -> dict:
        return {"ok": True}

def create_plugin() -> MyPlugin:
    return MyPlugin()
```

## 与 maibot-sdk 的对应

| maibot-sdk | provider-sdk |
|------------|--------------|
| `MaiBotPlugin` | `ProviderPlugin` |
| `@Tool` / `@Command` / `@API` | `@Route` / `@Hook` / `@API` |
| `create_plugin()` + `_manifest.json` | 相同 |
| `self.ctx.*` 能力代理 | `logger` / `config` / `http` |
| `@MessageGateway` | 无（Provider 非 IM Bot） |
| 平台相关 | `extensions.platform.PlatformAdapter`（可选） |

## 插件类型

| `plugin_type` | 说明 |
|---------------|------|
| `general`（默认） | 通用插件，声明 Route/Hook/API |
| `platform` | 额外提供 `PlatformAdapter`，供网关注册 |

## 示例

- `examples/hello_plugin/` — 通用插件
- `examples/echo_platform/` — 平台扩展插件

文档：[`docs/guide.md`](docs/guide.md)
