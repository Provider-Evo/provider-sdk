"""网关候选项类型 — 与 Provider Host ``Candidate`` 字段对齐。"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

__all__ = ["ALL_CAPABILITIES", "Candidate", "make_id"]

ALL_CAPABILITIES: tuple[str, ...] = (
    "chat",
    "completions",
    "vision",
    "image_gen",
    "image_edit",
    "image_variation",
    "video_gen",
    "audio_gen",
    "audio_in",
    "audio_transcription",
    "audio_translation",
    "embedding",
    "research",
    "thinking",
    "search",
    "code_exec",
    "artifacts",
    "tools",
    "native_tools",
    "upload",
    "uploads",
    "continuation",
    "moderation",
    "rerank",
    "batch",
    "fine_tuning",
    "files",
    "assistants",
    "threads",
    "runs",
    "vector_stores",
    "realtime",
    "responses",
    "anthropic_messages",
    "message_batches",
    "count_tokens",
    "conversations",
    "containers",
    "evals",
    "skills",
    "chatkit",
)


def make_id(platform: str, resource_id: str = "") -> str:
    """生成候选项 ID。

    Args:
        platform: 平台标识名。
        resource_id: 平台资源标识；提供时生成确定性 ID。

    Returns:
        格式为 ``{platform}_{hash12}`` 的 ID。
    """
    if resource_id:
        digest = hashlib.sha256(f"{platform}:{resource_id}".encode()).hexdigest()[:12]
        return f"{platform}_{digest}"
    return f"{platform}_{uuid.uuid4().hex[:12]}"


@dataclass
class Candidate:
    """候选项，包含能力布尔字段与元数据。"""

    id: str
    platform: str
    resource_id: str

    chat: bool = False
    completions: bool = False
    vision: bool = False
    tools: bool = False
    native_tools: bool = False
    thinking: bool = False
    search: bool = False
    continuation: bool = False

    image_gen: bool = False
    image_edit: bool = False
    image_variation: bool = False
    video_gen: bool = False
    audio_gen: bool = False

    audio_in: bool = False
    audio_transcription: bool = False
    audio_translation: bool = False

    embedding: bool = False
    rerank: bool = False

    research: bool = False
    code_exec: bool = False
    artifacts: bool = False
    moderation: bool = False
    responses: bool = False
    anthropic_messages: bool = False
    message_batches: bool = False
    count_tokens: bool = False
    conversations: bool = False
    containers: bool = False
    evals: bool = False
    skills: bool = False
    chatkit: bool = False

    upload: bool = False
    uploads: bool = False
    files: bool = False
    vector_stores: bool = False

    batch: bool = False
    fine_tuning: bool = False

    assistants: bool = False
    threads: bool = False
    runs: bool = False

    realtime: bool = False

    context_length: Optional[int] = None

    models: List[str] = field(default_factory=list)
    available: bool = True
    busy: bool = False
    cooldown: float = 0.0
    meta: Dict[str, Any] = field(default_factory=dict)

    def has_capability(self, cap: str) -> bool:
        """检查是否具备指定能力。"""
        return bool(getattr(self, cap, False))

    def to_model_dict(self, owned_by: str = "") -> Dict[str, Any]:
        """转换为 ``/v1/models`` 条目格式。"""
        caps: Dict[str, bool] = {}
        for cap in ALL_CAPABILITIES:
            if getattr(self, cap, False):
                caps[cap] = True
        result: Dict[str, Any] = {
            "object": "model",
            "created": int(time.time()),
            "owned_by": owned_by or self.platform,
            "capabilities": caps,
        }
        if self.context_length is not None:
            result["context_length"] = self.context_length
        return result
