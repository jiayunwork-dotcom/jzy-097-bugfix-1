"""评估编排：把几何、菲涅尔参数、第一区半径、损耗近似组装成结果。"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .fresnel import fresnel_parameter, wavelength_m
from .geometry import LinkGeometry
from .loss import knife_edge_loss_db
from .validation import validate_frequency, validate_geometry
from .zone import first_fresnel_radius_m


@dataclass(frozen=True)
class ParameterAssessment:
    """几何类结果：v、余隙、第一菲涅尔区半径。"""

    v: float
    clearance_m: float
    clearance_fresnel_ratio: float  # 余隙 / 第一菲涅尔区半径
    first_fresnel_radius_m: float
    wavelength_m: float


@dataclass(frozen=True)
class FullAssessment(ParameterAssessment):
    """在几何结果之上追加附加损耗与通视判定。"""

    loss_db: float
    is_los: bool


def _build_geometry(d1_m: float, d2_m: float, h_m: float) -> LinkGeometry:
    return validate_geometry(d1_m, d2_m, h_m)


def assess_parameters(
    d1_m: float, d2_m: float, h_m: float, frequency_mhz: float
) -> ParameterAssessment:
    """第一类调用：给定几何与频率，返回 v、余隙与第一菲涅尔区半径。"""
    geometry = _build_geometry(d1_m, d2_m, h_m)
    freq = validate_frequency(frequency_mhz)
    v = fresnel_parameter(geometry, freq)
    r1 = first_fresnel_radius_m(geometry, freq)
    clearance = geometry.clearance_m
    return ParameterAssessment(
        v=v,
        clearance_m=clearance,
        clearance_fresnel_ratio=clearance / r1,
        first_fresnel_radius_m=r1,
        wavelength_m=wavelength_m(freq),
    )


def assess_full(
    d1_m: float, d2_m: float, h_m: float, frequency_mhz: float
) -> FullAssessment:
    """第二类调用：在同样输入上进一步返回附加损耗与是否通视。"""
    base = assess_parameters(d1_m, d2_m, h_m, frequency_mhz)
    loss = knife_edge_loss_db(base.v)
    # 通视判定：障碍顶部低于直视线（v<0）才算几何通视；
    # 擦边（v=0）仍有约 6 dB 绕射损耗，不算通视。
    is_los = base.v < 0.0
    return FullAssessment(
        v=base.v,
        clearance_m=base.clearance_m,
        clearance_fresnel_ratio=base.clearance_fresnel_ratio,
        first_fresnel_radius_m=base.first_fresnel_radius_m,
        wavelength_m=base.wavelength_m,
        loss_db=loss,
        is_los=is_los,
    )
