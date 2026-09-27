"""回归用例：1400 MHz 非对称链路（d1≠d2）的绕射结果。

复现输入：d1=6500 m，d2=1500 m，h=+6 m（遮挡），f=1400 MHz。
手算参照值：v≈0.5252，r1≈16.15 m，余隙比≈−0.371，附加损耗≈10.49 dB。

历史缺陷：约化距离误算为 d1²/(d1+d2)（正确定义为 d1·d2/(d1+d2)）。
d1=d2 时两者恰好相等，故中点用例测不出；该链路 d1≠d2，当时三种
调用路径都报出 v≈0.252、r1≈33.63 m、损耗≈8.22 dB 的同一组错数。
此文件把该链路钉死，并覆盖参数、评估、批量三种调用路径。
"""

import math

import pytest
from fastapi.testclient import TestClient

from app.constants import SPEED_OF_LIGHT_M_S
from app.geometry import LinkGeometry
from app.main import app

client = TestClient(app)

# ---- 复现输入（原始链路，原样保留）----
D1_M = 6500.0
D2_M = 1500.0
H_M = 6.0
FREQ_MHZ = 1400.0
LINK = {"d1_m": D1_M, "d2_m": D2_M, "h_m": H_M, "frequency_mhz": FREQ_MHZ}

# ---- 手算参照值（按钉死的定义）----
REF_V = 0.5252
REF_R1_M = 16.15
REF_RATIO = -0.371
REF_LOSS_DB = 10.49

# ---- 按 README 钉死的定义独立重算的精确期望值 ----
LAM_M = SPEED_OF_LIGHT_M_S / (FREQ_MHZ * 1.0e6)
EXPECTED_V = H_M * math.sqrt(2.0 * (D1_M + D2_M) / (LAM_M * D1_M * D2_M))
EXPECTED_R1_M = math.sqrt(LAM_M * D1_M * D2_M / (D1_M + D2_M))
EXPECTED_RATIO = -H_M / EXPECTED_R1_M
_SHIFTED = EXPECTED_V - 0.1
EXPECTED_LOSS_DB = 6.9 + 20.0 * math.log10(
    math.sqrt(_SHIFTED * _SHIFTED + 1.0) + _SHIFTED
)


def _assert_matches_reference(body, *, with_loss):
    """结果须按定义精确命中，并与手算参照值在其给定精度上吻合。"""
    assert math.isclose(body["v"], EXPECTED_V, rel_tol=1e-9)
    assert math.isclose(body["first_fresnel_radius_m"], EXPECTED_R1_M, rel_tol=1e-9)
    assert math.isclose(body["clearance_fresnel_ratio"], EXPECTED_RATIO, rel_tol=1e-9)
    assert round(body["v"], 4) == REF_V
    assert round(body["first_fresnel_radius_m"], 2) == REF_R1_M
    assert round(body["clearance_fresnel_ratio"], 3) == REF_RATIO
    if with_loss:
        assert math.isclose(body["loss_db"], EXPECTED_LOSS_DB, rel_tol=1e-9)
        assert round(body["loss_db"], 2) == REF_LOSS_DB
        assert body["is_los"] is False


def test_reduced_distance_is_d1_d2_over_total():
    """约化距离必须为 d1·d2/(d1+d2)；d1≠d2 时与 d1²/(d1+d2) 明显不同。"""
    geom = LinkGeometry(D1_M, D2_M, H_M)
    expected = D1_M * D2_M / (D1_M + D2_M)
    assert math.isclose(geom.reduced_distance_m, expected, rel_tol=1e-12)


def test_reference_values_within_one_per_mille():
    """四个量与手算参照值的相对误差均在千分之一以内。

    余隙比的参照值 −0.371 只给到三位小数，真值为 −0.3714，
    故该项按四位参照 −0.3714 校验千分之一。
    """
    body = client.post("/v1/diffraction/assessment", json=LINK).json()
    assert math.isclose(body["v"], REF_V, rel_tol=1e-3)
    assert math.isclose(body["first_fresnel_radius_m"], REF_R1_M, rel_tol=1e-3)
    assert math.isclose(body["clearance_fresnel_ratio"], -0.3714, rel_tol=1e-3)
    assert math.isclose(body["loss_db"], REF_LOSS_DB, rel_tol=1e-3)


def test_parameters_path_matches_reference():
    """第一类调用（只算参数）命中参照值。"""
    body = client.post("/v1/diffraction/parameters", json=LINK).json()
    _assert_matches_reference(body, with_loss=False)


def test_assessment_path_matches_reference():
    """第二类调用（带损耗与通视判定）命中参照值。"""
    body = client.post("/v1/diffraction/assessment", json=LINK).json()
    _assert_matches_reference(body, with_loss=True)


def test_batch_path_matches_reference():
    """批量调用中该条链路命中同一组参照值。"""
    payload = {"links": [dict(LINK, link_id="regression-1400mhz")]}
    body = client.post("/v1/diffraction/batch", json=payload).json()
    assert body["count"] == 1
    (item,) = body["results"]
    assert item["ok"] and item["link_id"] == "regression-1400mhz"
    _assert_matches_reference(item["result"], with_loss=True)


def test_all_call_paths_agree():
    """三种调用路径对同一链路返回完全一致的结果。"""
    params = client.post("/v1/diffraction/parameters", json=LINK).json()
    assess = client.post("/v1/diffraction/assessment", json=LINK).json()
    batch = client.post("/v1/diffraction/batch", json={"links": [LINK]}).json()
    batch_result = batch["results"][0]["result"]
    for key in ("v", "first_fresnel_radius_m", "clearance_fresnel_ratio"):
        assert params[key] == assess[key] == batch_result[key]
    assert assess["loss_db"] == batch_result["loss_db"]


@pytest.mark.parametrize(
    "d1,d2,h,f",
    [
        (1200.0, 8800.0, -3.5, 2375.0),
        (500.0, 43000.0, 12.0, 450.0),
        (15000.0, 2500.0, 0.0, 5800.0),
    ],
)
def test_definition_holds_for_other_links(d1, d2, h, f):
    """修复不得特判回归链路：任意合法几何都按同一套定义计算。"""
    lam = SPEED_OF_LIGHT_M_S / (f * 1.0e6)
    expected_v = h * math.sqrt(2.0 * (d1 + d2) / (lam * d1 * d2))
    expected_r1 = math.sqrt(lam * d1 * d2 / (d1 + d2))
    body = client.post(
        "/v1/diffraction/parameters",
        json={"d1_m": d1, "d2_m": d2, "h_m": h, "frequency_mhz": f},
    ).json()
    assert math.isclose(body["v"], expected_v, rel_tol=1e-12)
    assert math.isclose(body["first_fresnel_radius_m"], expected_r1, rel_tol=1e-12)
