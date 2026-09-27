"""菲涅尔-基尔霍夫绕射参数 v。

定义（钉死）：
    v = h * sqrt(2 * (d1 + d2) / (lambda * d1 * d2))

其中 lambda 为波长，由频率换算。v 的符号完全由 h 决定：
障碍遮挡（h>0）则 v>0，余隙（h<0）则 v<0，擦边（h=0）则 v=0。
"""

from __future__ import annotations

import math

from .constants import SPEED_OF_LIGHT_M_S
from .geometry import LinkGeometry


def wavelength_m(frequency_mhz: float) -> float:
    """由频率（MHz）换算波长（m）。"""
    return SPEED_OF_LIGHT_M_S / (frequency_mhz * 1.0e6)


def fresnel_parameter(geometry: LinkGeometry, frequency_mhz: float) -> float:
    """计算菲涅尔-基尔霍夫参数 v。

    调用前须先经 validation 校验，保证距离与频率为正。
    """
    lam = wavelength_m(frequency_mhz)
    return geometry.h_m * math.sqrt(2.0 / (lam * geometry.reduced_distance_m))
