"""第一菲涅尔区半径。

在障碍所在截面处，第一菲涅尔区半径：
    r1 = sqrt(lambda * d1 * d2 / (d1 + d2))

用于把余隙折算成菲涅尔区单位，判断是否通视。
"""

from __future__ import annotations

import math

from .fresnel import wavelength_m
from .geometry import LinkGeometry


def first_fresnel_radius_m(geometry: LinkGeometry, frequency_mhz: float) -> float:
    """障碍截面处的第一菲涅尔区半径（m）。"""
    lam = wavelength_m(frequency_mhz)
    return math.sqrt(lam * geometry.reduced_distance_m)
