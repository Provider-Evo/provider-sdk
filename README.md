# provider-sdk

Provider-V2 平台插件 SDK。对标 [maibot-plugin-sdk](https://github.com/Mai-with-u/maibot-plugin-sdk) 的插件契约，为第三方**平台适配器**提供独立开发与加载能力。

## 安装

```bash
pip install -e X:\Project\provider-sdk
```

## 快速开始

在 Provider Host 的 `plugins/` 目录下创建插件文件夹：

```
plugins/
  my_platform/
    _manifest.json
    plugin.py
    config.toml          # 可选，由 Host 管理
```

`plugin.py` 最小示例见 [`examples/echo_platform/plugin.py`](examples/echo_platform/plugin.py)。

```python
from provider_sdk import ProviderPlugin, PlatformAdapter, Candidate, make_id

class MyPlugin(ProviderPlugin, PlatformAdapter):
    @property
    def name(self) -> str:
        return "my_platform"

    async def on_load(self) -> None:
        self.ctx.logger.info("loaded")

    async def init(self, session): ...
    async def candidates(self) -> list[Candidate]: ...
    async def ensure_candidates(self, count: int) -> int: ...
    async def complete(self, candidate, messages, model, stream, **kw): ...
    async def close(self) -> None: ...

def create_plugin() -> MyPlugin:
    return MyPlugin()
```

## 与 MaiBot SDK 的对应关系

| MaiBot | provider-sdk |
|--------|----------------|
| `MaiBotPlugin` | `ProviderPlugin` |
| `create_plugin()` | `create_plugin()` |
| `_manifest.json` | `_manifest.json` |
| `on_load` / `on_unload` / `on_config_update` | 相同 |
| `self.ctx.send` / `gateway` 等 | `self.ctx.config` / `http` / `logger` |
| `@Tool` / `@Command` | 平台插件以 `PlatformAdapter` 能力为主 |

## Host 集成

```python
from pathlib import Path
from provider_sdk.integrate import load_platform_plugins, register_loaded_plugins

loaded = await load_platform_plugins(Path("plugins"), session)
register_loaded_plugins(registry, loaded)
```

完整说明见 [`docs/guide.md`](docs/guide.md)。

## 开发

```bash
pip install -e ".[dev]"
pytest -q
```
