"""插件配置模型与校验工具。"""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from typing import Any, ClassVar, TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "Field",
    "PluginConfigBase",
    "build_plugin_default_config",
    "is_plugin_config_class",
    "merge_plugin_config_data",
    "validate_plugin_config",
]

PluginConfigT = TypeVar("PluginConfigT", bound="PluginConfigBase")


class PluginConfigBase(BaseModel):
    """插件配置模型基类。

    插件作者继承此类声明配置结构；Host 据此生成默认配置与 WebUI Schema。
    """

    model_config = ConfigDict(validate_assignment=True, extra="ignore")

    __ui_label__: ClassVar[str] = ""
    __ui_icon__: ClassVar[str] = ""
    __ui_order__: ClassVar[int] = 0


def is_plugin_config_class(candidate: Any) -> bool:
    """判断对象是否为插件配置模型类。"""
    return bool(inspect.isclass(candidate) and issubclass(candidate, PluginConfigBase))


def build_plugin_default_config(config_class: type[PluginConfigT]) -> dict[str, Any]:
    """根据配置模型构造默认配置字典。"""
    try:
        instance = config_class()
    except Exception as exc:
        raise ValueError(
            f"插件配置模型 {config_class.__name__} 需要为所有字段提供默认值"
        ) from exc
    return instance.model_dump(mode="python")


def validate_plugin_config(
    config_class: type[PluginConfigT],
    config_data: Mapping[str, Any],
) -> PluginConfigT:
    """校验并构造强类型配置实例。"""
    return config_class.model_validate(dict(config_data))


def merge_plugin_config_data(
    default_config: Mapping[str, Any],
    raw_config: Mapping[str, Any],
) -> tuple[dict[str, Any], bool]:
    """将用户配置递归合并到默认配置之上。"""
    changed = False
    merged: dict[str, Any] = dict(default_config)

    for key, value in raw_config.items():
        base_value = merged.get(key)
        if isinstance(base_value, Mapping) and isinstance(value, Mapping):
            nested, nested_changed = merge_plugin_config_data(base_value, value)
            merged[key] = nested
            changed = changed or nested_changed or nested != dict(base_value)
        elif base_value != value:
            merged[key] = value
            changed = True

    return merged, changed
