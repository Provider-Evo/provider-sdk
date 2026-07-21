"""Backward-compat re-export — prefer ``provider_sdk.types.model_ids``."""
from __future__ import annotations

from provider_sdk.types.model_ids import *  # noqa: F403
from provider_sdk.types.model_ids import (
    ModelIdRegistry,
    build_model_id_maps,
    upstream_to_public_id,
)

__all__ = [
    "ModelIdRegistry",
    "build_model_id_maps",
    "upstream_to_public_id",
]
