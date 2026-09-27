"""菲涅尔参数 v 的核心关系测试。"""

import math

from app.fresnel import fresnel_parameter, wavelength_m
from app.geometry import LinkGeometry

GEOM = LinkGeometry(d1_m=3000.0, d2_m=4000.0, h_m=8.0)


def test_grazing_obstacle_gives_zero_v():
    """障碍恰好擦着直视线（h=0）时 v=0。"""
    grazing = LinkGeometry(d1_m=3000.0, d2_m=4000.0, h_m=0.0)
    assert fresnel_parameter(grazing, 900.0) == 0.0


def test_v_sign_follows_h_sign():
    """符号约定：遮挡为正、余隙为负，绝不能反。"""
    above = fresnel_parameter(LinkGeometry(3000.0, 4000.0, 5.0), 900.0)
    below = fresnel_parameter(LinkGeometry(3000.0, 4000.0, -5.0), 900.0)
    assert above > 0.0
    assert below < 0.0
    assert above == -below


def test_doubling_frequency_scales_v_by_sqrt2():
    """同一几何下只把频率加倍，v 按频率的平方根变化。"""
    f1 = 450.0
    f2 = 900.0
    v1 = fresnel_parameter(GEOM, f1)
    v2 = fresnel_parameter(GEOM, f2)
    assert v2 == v1 * math.sqrt(f2 / f1)
    assert math.isclose(v2 / v1, math.sqrt(2.0), rel_tol=1e-12)


def test_v_monotonic_in_h():
    """只把障碍加高，v 随之增大。"""
    v_low = fresnel_parameter(LinkGeometry(3000.0, 4000.0, 2.0), 900.0)
    v_high = fresnel_parameter(LinkGeometry(3000.0, 4000.0, 12.0), 900.0)
    assert v_high > v_low


def test_wavelength_conversion():
    """900 MHz 对应波长约 0.333 m。"""
    assert math.isclose(wavelength_m(900.0), 299_792_458.0 / 9.0e8, rel_tol=1e-12)
