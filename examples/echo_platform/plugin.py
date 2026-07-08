"""Echo 示例平台插件 — 演示 provider-sdk 最小实现。"""

from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, List, Union

import aiohttp

from provider_sdk import (
    Candidate,
    Field,
    PlatformAdapter,
    PluginConfigBase,
    ProviderPlugin,
    make_id,
)


class EchoPluginConfig(PluginConfigBase):
    """Echo 插件配置。"""

    __ui_label__ = "Echo"
    __ui_icon__ = "message-square"
    __ui_order__ = 0

    enabled: bool = Field(default=True, description="是否启用")
    prefix: str = Field(default="[echo] ", description="回显前缀")


class EchoPlatformPlugin(ProviderPlugin, PlatformAdapter):
    """将最后一条 user 消息原样回显。"""

    config_model = EchoPluginConfig

    def __init__(self) -> None:
        super().__init__()
        self._ready = False

    @property
    def name(self) -> str:
        return "echo"

    @property
    def supported_models(self) -> List[str]:
        return ["echo"]

    async def on_load(self) -> None:
        self.ctx.logger.info("Echo 平台插件已加载")

    async def init(self, session: aiohttp.ClientSession) -> None:
        del session
        self._ready = True

    async def candidates(self) -> List[Candidate]:
        if not self._ready:
            return []
        return [
            Candidate(
                id=make_id(self.name, "default"),
                platform=self.name,
                resource_id="default",
                chat=True,
                models=["echo"],
            )
        ]

    async def ensure_candidates(self, count: int) -> int:
        items = await self.candidates()
        return min(len(items), count)

    async def complete(
        self,
        candidate: Candidate,
        messages: List[Dict[str, Any]],
        model: str,
        stream: bool,
        *,
        thinking: bool = False,
        search: bool = False,
        **kw: Any,
    ) -> AsyncGenerator[Union[str, Dict[str, Any]], None]:
        del candidate, model, thinking, search, kw
        text = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                text = content if isinstance(content, str) else str(content)
                break

        cfg = self.get_plugin_config_data()
        prefix = str(cfg.get("prefix") or "[echo] ")
        if not prefix and self.has_config_model():
            try:
                prefix = self.config.prefix
            except RuntimeError:
                prefix = "[echo] "

        reply = f"{prefix}{text}"
        if stream:
            for ch in reply:
                yield ch
        else:
            yield reply

    async def close(self) -> None:
        self._ready = False


def create_plugin() -> EchoPlatformPlugin:
    """插件工厂函数 — Host 通过此入口实例化插件。"""
    return EchoPlatformPlugin()
