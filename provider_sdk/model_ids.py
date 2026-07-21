from __future__ import annotations

"""平台模型 ID 公开名与上游名双向映射。

规则（按优先级）：
1. Cloudflare ``@cf/vendor/model`` → ``cf-vendor-model``（``/``、版本 ``.`` 归一化为 ``-``）
2. 版本号 ``\\d.\\d`` → ``\\d-\\d``（如 ``qwen3.7-max`` → ``qwen3-7-max``）
3. OpenRouter 风格 ``org/model:tier`` → ``org-model-tier``（``/``、``:`` → ``-``）
4. 不透明 ID（长 hex / 纯数字）→ ``{prefix}-{sha8}``，并保留上游映射
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Union

_VERSION_DOT = re.compile(r"(\d)\.(\d)")
_CF_PREFIX = re.compile(r"^@cf/", re.IGNORECASE)
_SLUG_SAFE = re.compile(r"[^a-z0-9]+")
_OPAQUE_HEX = re.compile(r"^[a-f0-9-]{32,}$", re.IGNORECASE)
_OPAQUE_DIGITS = re.compile(r"^\d{10,}$")


def _slugify(text: str, *, max_len: int = 96) -> str:
    slug = _SLUG_SAFE.sub("-", text.lower()).strip("-")
    if not slug:
        return ""
    return slug[:max_len].strip("-")


def _is_opaque_segment(segment: str) -> bool:
    if not segment:
        return False
    if _OPAQUE_DIGITS.match(segment):
        return True
    if len(segment) >= 32 and _OPAQUE_HEX.match(segment):
        return True
    return False


def upstream_to_public_id(
    upstream: str,
    *,
    display_name: Optional[str] = None,
) -> str:
    """将上游模型 ID 转为对外暴露的统一风格。"""
    upstream = (upstream or "").strip()
    if not upstream:
        return upstream

    if display_name:
        named = _slugify(display_name)
        if named and not _is_opaque_segment(named):
            return named

    if _CF_PREFIX.match(upstream):
        body = upstream[4:]
        parts = [p for p in body.split("/") if p]
        if parts and _is_opaque_segment(parts[-1]) and len(parts) >= 2:
            prefix = _slugify(parts[-2]) or "cf"
            digest = hashlib.sha256(upstream.encode("utf-8")).hexdigest()[:8]
            return f"cf-{prefix}-{digest}"
        slug = _slugify(body.replace("/", "-"))
        slug = _VERSION_DOT.sub(r"\1-\2", slug)
        if slug.startswith("cf-"):
            return slug
        return f"cf-{slug}" if slug else upstream

    if "/" in upstream or ":" in upstream:
        normalized = upstream.replace("/", "-").replace(":", "-")
        normalized = _VERSION_DOT.sub(r"\1-\2", normalized)
        return normalized.strip("-")

    if _is_opaque_segment(upstream):
        digest = hashlib.sha256(upstream.encode("utf-8")).hexdigest()[:8]
        return f"model-{digest}"

    return _VERSION_DOT.sub(r"\1-\2", upstream)


def build_model_id_maps(
    upstream_ids: Iterable[str],
    *,
    display_names: Optional[Mapping[str, str]] = None,
) -> tuple[List[str], Dict[str, str], Dict[str, str]]:
    """从上游 ID 列表构建公开 ID 列表与双向映射。"""
    public_ids: List[str] = []
    public_to_upstream: Dict[str, str] = {}
    upstream_to_public: Dict[str, str] = {}
    seen_public: set[str] = set()
    names = display_names or {}

    for upstream in upstream_ids:
        if not upstream:
            continue
        public = upstream_to_public_id(upstream, display_name=names.get(upstream))
        if public in seen_public and public_to_upstream.get(public) != upstream:
            suffix = hashlib.sha256(upstream.encode("utf-8")).hexdigest()[:6]
            public = f"{public}-{suffix}"
        public_to_upstream[public] = upstream
        public_to_upstream[upstream] = upstream
        upstream_to_public[upstream] = public
        if public not in seen_public:
            seen_public.add(public)
            public_ids.append(public)
    return public_ids, public_to_upstream, upstream_to_public


def _default_persist_path(platform: str) -> Path:
    try:
        from src.foundation.paths import persist_dir
    except ImportError:
        return Path("persist") / platform / "model_id_map.json"
    return persist_dir(platform) / "model_id_map.json"


class ModelIdRegistry:
    """平台内模型 ID 注册表：公开名暴露、上游名请求。"""

    def __init__(self, platform: str, *, persist: bool = True) -> None:
        self.platform = platform
        self._persist = persist
        self._persist_path = _default_persist_path(platform)
        self._public_to_upstream: Dict[str, str] = {}
        self._upstream_to_public: Dict[str, str] = {}
        self._public_ids: List[str] = []

    @property
    def public_models(self) -> List[str]:
        return list(self._public_ids)

    @property
    def public_to_upstream(self) -> Dict[str, str]:
        return dict(self._public_to_upstream)

    def load(self) -> None:
        if not self._persist_path.is_file():
            return
        try:
            data = json.loads(self._persist_path.read_text(encoding="utf-8"))
            raw = data.get("public_to_upstream", {})
            if isinstance(raw, dict):
                self._public_to_upstream.update(
                    {str(k): str(v) for k, v in raw.items() if k and v}
                )
                for public, upstream in raw.items():
                    if public != upstream:
                        self._upstream_to_public[str(upstream)] = str(public)
        except Exception:
            return

    def save(self) -> None:
        if not self._persist:
            return
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "platform": self.platform,
                "public_to_upstream": self._public_to_upstream,
                "public_models": self._public_ids,
            }
            self._persist_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            return

    def register_many(
        self,
        upstream_ids: Iterable[str],
        *,
        display_names: Optional[Mapping[str, str]] = None,
    ) -> List[str]:
        public_ids, p2u, u2p = build_model_id_maps(
            upstream_ids, display_names=display_names
        )
        self._public_to_upstream.update(p2u)
        self._upstream_to_public.update(u2p)
        self._public_ids = public_ids
        self.save()
        return list(public_ids)

    def register_catalog(
        self,
        items: Sequence[Union[str, Dict[str, Any]]],
    ) -> List[str]:
        upstream_ids: List[str] = []
        display_names: Dict[str, str] = {}
        for item in items:
            if isinstance(item, str):
                upstream_ids.append(item)
                continue
            if not isinstance(item, dict):
                continue
            upstream = (
                item.get("id")
                or item.get("model")
                or item.get("modelId")
                or item.get("slug")
                or ""
            )
            if not isinstance(upstream, str) or not upstream:
                continue
            upstream_ids.append(upstream)
            for key in ("name", "display_name", "title", "label"):
                val = item.get(key)
                if isinstance(val, str) and val.strip():
                    display_names[upstream] = val.strip()
                    break
        return self.register_many(upstream_ids, display_names=display_names or None)

    def resolve_upstream(self, model: str) -> str:
        if not model:
            return model
        mapped = self._public_to_upstream.get(model)
        if mapped:
            return mapped
        if model in self._upstream_to_public:
            return model
        return model

    def merge_fallback(self, upstream_ids: Iterable[str]) -> List[str]:
        """合并静态兜底列表，不覆盖已有映射。"""
        existing_upstream = {
            v for k, v in self._public_to_upstream.items() if k != v
        }
        merged = list(existing_upstream)
        for upstream in upstream_ids:
            if upstream and upstream not in merged:
                merged.append(upstream)
        return self.register_many(merged)
