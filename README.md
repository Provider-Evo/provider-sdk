# provider-sdk

Provider-V2 **通用插件 SDK**。

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

## 核心概念

| 概念 | 说明 |
|------|------|
| `ProviderPlugin` | 插件基类，生命周期 + 配置 |
| `create_plugin()` | 模块级工厂函数 |
| `_manifest.json` | 插件元数据与依赖 |
| `@Route` / `@Hook` / `@API` | 向 Host 声明组件 |
| `self.ctx` | 运行时上下文（日志 / 配置 / HTTP） |

## 插件类型

| `plugin_type` | 说明 |
|---------------|------|
| `general`（默认） | 通用插件，声明 Route/Hook/API |
| `platform` | 额外提供 `PlatformAdapter`，供网关注册 |

## 示例

- `examples/hello_plugin/` — 通用插件
- `examples/echo_platform/` — 平台扩展插件

文档：[`docs/guide.md`](docs/guide.md)
