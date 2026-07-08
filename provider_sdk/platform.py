"""平台适配器抽象接口 — 与 Provider Host 内置适配器契约一致。"""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import aiohttp

from provider_sdk.types.candidate import Candidate

__all__ = ["PlatformAdapter", "DEFAULT_CONTEXT_LENGTH"]

DEFAULT_CONTEXT_LENGTH = 131072


class PlatformAdapter(ABC):
    """所有平台适配器的抽象基类。

  设计原则（与 Host 一致）：

  - ``init()`` 必须立即返回，耗时操作放后台 Task
  - ``candidates()`` 随时反映真实状态
  - 可选能力方法有安全默认实现
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """平台标识名（小写，建议与目录名一致）。"""
        ...

    @property
    def supported_models(self) -> List[str]:
        """支持的模型列表。"""
        return []

    @property
    def default_capabilities(self) -> Dict[str, bool]:
        """默认能力字典，用于 ``/v1/models`` 输出。"""
        return {"chat": True}

    @property
    def context_length(self) -> Optional[int]:
        """默认上下文长度。"""
        return DEFAULT_CONTEXT_LENGTH

    @abstractmethod
    async def init(self, session: aiohttp.ClientSession) -> None:
        """初始化适配器，必须立即返回。"""
        ...

    @abstractmethod
    async def candidates(self) -> List[Candidate]:
        """返回当前可用候选项列表。"""
        ...

    @abstractmethod
    async def ensure_candidates(self, count: int) -> int:
        """确保至少有 ``count`` 个候选项可用。"""
        ...

    @abstractmethod
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
        """聊天补全，yield 文本增量或结构化事件。"""
        ...

    @abstractmethod
    async def close(self) -> None:
        """关闭适配器并释放资源。"""
        ...

    async def fetch_remote_models(self) -> List[str]:
        """拉取远程模型列表。"""
        return []

    async def create_embedding(
        self,
        candidate: Candidate,
        input_data: Union[str, List[str]],
        model: str,
        **kw: Any,
    ) -> Dict[str, Any]:
        inputs = [input_data] if isinstance(input_data, str) else list(input_data)
        return {
            "object": "list",
            "data": [
                {"object": "embedding", "index": i, "embedding": []}
                for i, _ in enumerate(inputs)
            ],
            "model": model,
            "usage": {"prompt_tokens": 0, "total_tokens": 0},
        }

    async def create_image(
        self,
        candidate: Candidate,
        prompt: str,
        model: str,
        **kw: Any,
    ) -> Dict[str, Any]:
        return {"created": int(time.time()), "data": []}

    async def create_moderation(
        self,
        candidate: Candidate,
        input_data: Union[str, List[str]],
        model: str,
        **kw: Any,
    ) -> Dict[str, Any]:
        inputs = [input_data] if isinstance(input_data, str) else list(input_data)
        return {
            "id": f"modr-{uuid.uuid4().hex[:24]}",
            "model": model,
            "results": [{"flagged": False, "categories": {}, "category_scores": {}} for _ in inputs],
        }

    def set_proxy_enabled(self, enabled: bool) -> None:
        """设置代理覆盖开关（可选）。"""
        del enabled

    def is_proxy_allowed(self) -> bool:
        """是否允许代理切换。"""
        return False

    def is_proxy_enabled(self) -> bool:
        """当前是否启用代理。"""
        return False
