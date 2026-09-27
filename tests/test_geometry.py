"""几何、余隙与第一菲涅尔区半径测试。"""

import math

import pytest

from app.geometry import LinkGeometry
from app.service import assess_full, assess_parameters
from app.validation import ValidationError, validate_frequency, validate_geometry
from app.zone import first_fresnel_radius_m


def test_clearance_is_negative_of_h():
    """余隙与 h 符号相反：遮挡时余隙为负。"""
    assert LinkGeometry(1000.0, 1000.0, 5.0).clearance_m == -5.0
    assert LinkGeometry(1000.0, 1000.0, -5.0).clearance_m == 5.0


def test_first_fresnel_radius_midpoint():
    """d1=d2 时 r1 = sqrt(lambda*d/2)，取 900 MHz、d1=d2=2 km 校验。"""
    geom = LinkGeometry(2000.0, 2000.0, 0.0)
    lam = 299_792_458.0 / 9.0e8
    expected = math.sqrt(lam * 2000.0 * 2000.0 / 4000.0)
    assert math.isclose(first_fresnel_radius_m(geom, 900.0), expected, rel_tol=1e-12)


def test_deep_clearance_full_assessment_zero_loss_and_los():
    """d1=d2 且障碍显著低于直视线：损耗趋零、判定通视。"""
    a = assess_full(d1_m=2000.0, d2_m=2000.0, h_m=-100.0, frequency_mhz=900.0)
    assert a.v <= -0.78
    assert a.loss_db == 0.0
    assert a.is_los is True
    assert a.clearance_m == 100.0


def test_obstructed_assessment_not_los():
    a = assess_full(d1_m=3000.0, d2_m=4000.0, h_m=8.0, frequency_mhz=900.0)
    assert a.is_los is False
    assert a.loss_db > 6.0


def test_assess_parameters_reports_radius_and_clearance():
    a = assess_parameters(d1_m=3000.0, d2_m=4000.0, h_m=8.0, frequency_mhz=900.0)
    assert a.first_fresnel_radius_m > 0.0
    assert a.clearance_m == -8.0
    # 余隙/半径 与 v 的关系：clearance/r1 = -v/sqrt(2)
    assert math.isclose(a.clearance_fresnel_ratio, -a.v / math.sqrt(2.0), rel_tol=1e-9)


@pytest.mark.parametrize("field", ["d1_m", "d2_m"])
@pytest.mark.parametrize("bad", [0.0, -1.0, float("inf"), float("nan")])
def test_non_positive_or_nonfinite_distance_rejected(field, bad):
    kwargs = dict(d1_m=1000.0, d2_m=1000.0, h_m=0.0)
    kwargs[field] = bad
    with pytest.raises(ValidationError) as excinfo:
        validate_geometry(**kwargs)
    assert field in excinfo.value.reason


@pytest.mark.parametrize("bad", [0.0, -900.0, float("inf"), float("nan")])
def test_non_positive_frequency_rejected(bad):
    with pytest.raises(ValidationError) as excinfo:
        validate_frequency(bad)
    assert "frequency_mhz" in excinfo.value.reason
