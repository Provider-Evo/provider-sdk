# Provider 平台插件开发指南

## 边界

- 插件代码**不得** `import src.*`（Provider Host 内部模块）
- 唯一依赖：`provider-sdk`
- 入口文件必须是 `plugin.py`
- 必须导出模块级 `create_plugin()` 工厂函数

## 目录结构

```
plugins/<plugin-name>/
  _manifest.json    # 元数据（必填）
  plugin.py         # 入口（必填）
  config.toml       # 插件配置（Host 写入，可选）
```

## Manifest

```json
{
  "manifest_version": 1,
  "id": "your-name.my-platform",
  "name": "My Platform",
  "version": "0.1.0",
  "plugin_type": "platform",
  "sdk": { "min_version": "0.1.0", "max_version": "0.99.99" },
  "dependencies": []
}
```

- `id`：全局唯一，建议 `作者.插件名` 格式
- `plugin_type`：平台适配器固定为 `platform`
- `dependencies`：其他插件 ID，加载顺序按拓扑排序

## 插件基类

继承 `ProviderPlugin` 并实现三个生命周期方法：

| 方法 | 说明 |
|------|------|
| `on_load()` | 上下文注入后调用 |
| `on_unload()` | 卸载前调用 |
| `on_config_update(scope, config_data, version)` | 热重载；`scope=self` 为插件配置 |

## 平台适配器

推荐**单类**同时继承 `ProviderPlugin` 与 `PlatformAdapter`：

```python
class MyPlugin(ProviderPlugin, PlatformAdapter):
    ...
```

或实现 `get_adapter()` 返回独立适配器实例。

### 必须实现的方法

- `name` — 平台标识（小写）
- `init(session)` — 立即返回，后台初始化
- `candidates()` — 当前候选项
- `ensure_candidates(count)`
- `complete(...)` — 异步生成器
- `close()`

候选项类型使用 `provider_sdk.Candidate` 与 `make_id()`。

## 配置模型

```python
from provider_sdk import Field, PluginConfigBase

class MyConfig(PluginConfigBase):
    enabled: bool = Field(default=True)
    api_base: str = Field(default="https://api.example.com")

class MyPlugin(ProviderPlugin, PlatformAdapter):
    config_model = MyConfig
```

运行时通过 `self.config` 访问强类型配置（需 Host 注入配置后）。

## 运行时上下文 `self.ctx`

| 成员 | 说明 |
|------|------|
| `ctx.logger` | 标准 `logging.Logger` |
| `ctx.config.get_plugin()` | 插件配置字典 |
| `ctx.config.get_global()` | Host 全局配置 |
| `ctx.http.session` | 共享 `aiohttp.ClientSession` |
| `ctx.plugin_id` | manifest id |
| `ctx.paths["plugin_dir"]` | 插件目录绝对路径 |

## Host 加载流程

1. 扫描 `plugins/*/ _manifest.json`
2. 解析依赖并拓扑排序
3. `import plugin.py` → `create_plugin()`
4. 校验 `ProviderPlugin` + `PlatformAdapter`
5. 注入 `PluginContext`，调用 `on_load()`
6. 调用 `adapter.init(session)` 并注册到网关 Registry

使用 `provider_sdk.runtime.PluginLoader` 或 `provider_sdk.integrate.load_platform_plugins`。

## 示例

见仓库 `examples/echo_platform/`：将用户最后一条消息带前缀回显。

```bash
pytest tests/test_loader.py -q
```
