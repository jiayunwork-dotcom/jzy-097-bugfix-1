"""输入校验。

距离不为正、频率不为正、或非有限数值，一律抛出 ValidationError，
由接口层转成带原因的错误 JSON 拒绝。
"""

from __future__ import annotations

import math

from .geometry import LinkGeometry


class ValidationError(ValueError):
    """输入不合法。reason 字段给出可读的拒绝原因。"""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _require_finite_positive(name: str, value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError(f"{name} 必须是数值，收到 {value!r}")
    if not math.isfinite(value):
        raise ValidationError(f"{name} 必须是有限数值，收到 {value!r}")
    if value <= 0.0:
        raise ValidationError(f"{name} 必须为正数，收到 {value!r}")
    return float(value)


def _require_finite(name: str, value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError(f"{name} 必须是数值，收到 {value!r}")
    if not math.isfinite(value):
        raise ValidationError(f"{name} 必须是有限数值，收到 {value!r}")
    return float(value)


def validate_geometry(d1_m: float, d2_m: float, h_m: float) -> LinkGeometry:
    """校验并构造链路几何。d1、d2 必须为正，h 必须有限（符号任意）。"""
    return LinkGeometry(
        d1_m=_require_finite_positive("d1_m", d1_m),
        d2_m=_require_finite_positive("d2_m", d2_m),
        h_m=_require_finite("h_m", h_m),
    )


def validate_frequency(frequency_mhz: float) -> float:
    """校验频率（MHz），必须为正。"""
    return _require_finite_positive("frequency_mhz", frequency_mhz)
