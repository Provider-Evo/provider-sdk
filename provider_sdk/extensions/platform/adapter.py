"""平台适配器抽象接口 — 可选扩展，供 platform 类型插件使用。"""

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
    """平台适配器接口（可选插件扩展）。"""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    def supported_models(self) -> List[str]:
        return []

    @property
    def default_capabilities(self) -> Dict[str, bool]:
        return {"chat": True}

    @property
    def context_length(self) -> Optional[int]:
        return DEFAULT_CONTEXT_LENGTH

    @abstractmethod
    async def init(self, session: aiohttp.ClientSession) -> None:
        ...

    @abstractmethod
    async def candidates(self) -> List[Candidate]:
        ...

    @abstractmethod
    async def ensure_candidates(self, count: int) -> int:
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
        ...

    @abstractmethod
    async def close(self) -> None:
        ...

    async def fetch_remote_models(self) -> List[str]:
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
        del enabled

    def is_proxy_allowed(self) -> bool:
        return False

    def is_proxy_enabled(self) -> bool:
        return False
