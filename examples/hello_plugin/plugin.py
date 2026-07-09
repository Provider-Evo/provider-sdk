"""Hello 通用插件示例。"""

from __future__ import annotations

from typing import Any

from provider_sdk import API, Field, Hook, PluginConfigBase, ProviderPlugin, Route


class HelloConfig(PluginConfigBase):
    greeting: str = Field(default="你好，Provider 插件！", description="问候语")


class HelloPlugin(ProviderPlugin):
    config_model = HelloConfig

    async def on_load(self) -> None:
        self.ctx.logger.info("Hello 插件已加载")

    async def on_unload(self) -> None:
        self.ctx.logger.info("Hello 插件已卸载")

    @Route("/plugins/hello", methods=["GET"], description="返回问候 JSON")
    async def hello_route(self) -> dict[str, str]:
        try:
            text = self.config.greeting
        except RuntimeError:
            text = str(self.get_plugin_config_data().get("greeting", "你好"))
        return {"message": text}

    @Hook("gateway.request.before", description="请求前日志")
    async def before_request(self, **kwargs: Any) -> None:
        model = kwargs.get("model", "")
        self.ctx.logger.debug("gateway 请求: model=%s", model)

    @API("ping", description="健康检查", public=True)
    async def ping(self) -> dict[str, bool]:
        return {"ok": True}


def create_plugin() -> HelloPlugin:
    return HelloPlugin()
