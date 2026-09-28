"""回归用例：1400 MHz 不对称链路（d1=6500 m, d2=1500 m, h=6 m）。

背景：reduced_distance_m 一度被错写成 d1·(1 - d2/(d1+d2)) = d1²/(d1+d2)，
丢掉了一个 d2，导致非对称几何下 v、第一菲涅尔区半径、余隙比与附加损耗
整体报错（d1=d2 时错式恰好与定义重合，所以旧用例没拦住）。

本用例按服务说明中钉死的定义从第一性原理重算期望值：
    λ   = c / f
    v   = h·√(2·(d1+d2)/(λ·d1·d2))
    r1  = √(λ·d1·d2/(d1+d2))
    余隙比 = -h / r1
    J(v)= 6.9 + 20·log10(√((v-0.1)²+1) + v - 0.1)
并要求 parameters / assessment / batch 三种调用路径返回完全一致的结果，
相对误差均在千分之一以内。
"""

import math

from fastapi.testclient import TestClient

from app.constants import SPEED_OF_LIGHT_M_S
from app.loss import knife_edge_loss_db
from app.main import app
from app.service import assess_full, assess_parameters

client = TestClient(app)

# ---- 复现链路 ----
D1, D2, H, F_MHZ = 6500.0, 1500.0, 6.0, 1400.0
LINK = {"d1_m": D1, "d2_m": D2, "h_m": H, "frequency_mhz": F_MHZ}

REL_TOL = 1e-3

# 用户手算（按定义）的参照值
REF_V = 0.5252
REF_R1 = 16.15
REF_RATIO = -0.371
REF_LOSS_DB = 10.49


def _expected(d1, d2, h, f_mhz):
    """直接按文档定义从第一性原理计算，独立于生产代码路径。"""
    lam = SPEED_OF_LIGHT_M_S / (f_mhz * 1.0e6)
    v = h * math.sqrt(2.0 * (d1 + d2) / (lam * d1 * d2))
    r1 = math.sqrt(lam * d1 * d2 / (d1 + d2))
    ratio = -h / r1
    loss = knife_edge_loss_db(v)
    return lam, v, r1, ratio, loss


LAM, V, R1, RATIO, LOSS = _expected(D1, D2, H, F_MHZ)


def test_reference_constants():
    """期望值本身就是用户给出的参照数（允许末位舍入）。"""
    assert round(V, 4) == REF_V
    assert round(R1, 2) == REF_R1
    assert round(RATIO, 3) == REF_RATIO
    assert round(LOSS, 2) == REF_LOSS_DB


def test_parameters_call_matches_definition():
    """parameters 类调用：v、r1、余隙比、波长与定义吻合到千分之一以内。"""
    a = assess_parameters(D1, D2, H, F_MHZ)
    assert math.isclose(a.v, V, rel_tol=REL_TOL)
    assert math.isclose(a.first_fresnel_radius_m, R1, rel_tol=REL_TOL)
    assert math.isclose(a.clearance_fresnel_ratio, RATIO, rel_tol=REL_TOL)
    assert math.isclose(a.wavelength_m, LAM, rel_tol=REL_TOL)
    assert a.clearance_m == -H
    # 恒等式 clearance/r1 = -v/√2，与定义自洽
    assert math.isclose(a.clearance_fresnel_ratio, -a.v / math.sqrt(2.0), rel_tol=1e-9)


def test_full_call_matches_definition():
    """带损耗与通视判定的调用：附加损耗 10.49 dB，遮挡故非通视。"""
    a = assess_full(D1, D2, H, F_MHZ)
    assert math.isclose(a.v, V, rel_tol=REL_TOL)
    assert math.isclose(a.first_fresnel_radius_m, R1, rel_tol=REL_TOL)
    assert math.isclose(a.clearance_fresnel_ratio, RATIO, rel_tol=REL_TOL)
    assert math.isclose(a.loss_db, LOSS, rel_tol=REL_TOL)
    assert math.isclose(a.loss_db, REF_LOSS_DB, rel_tol=REL_TOL)
    assert a.is_los is False  # h>0 遮挡


def test_http_parameters_endpoint():
    body = client.post("/v1/diffraction/parameters", json=LINK).json()
    assert math.isclose(body["v"], V, rel_tol=REL_TOL)
    assert math.isclose(body["first_fresnel_radius_m"], R1, rel_tol=REL_TOL)
    assert math.isclose(body["clearance_fresnel_ratio"], RATIO, rel_tol=REL_TOL)
    assert "loss_db" not in body


def test_http_assessment_endpoint():
    body = client.post("/v1/diffraction/assessment", json=LINK).json()
    assert math.isclose(body["v"], V, rel_tol=REL_TOL)
    assert math.isclose(body["first_fresnel_radius_m"], R1, rel_tol=REL_TOL)
    assert math.isclose(body["clearance_fresnel_ratio"], RATIO, rel_tol=REL_TOL)
    assert math.isclose(body["loss_db"], LOSS, rel_tol=REL_TOL)
    assert body["is_los"] is False


def test_http_batch_endpoint_agrees():
    """塞进一批里一起算，该条结果与单条一致，且不被同批其他链路影响。"""
    payload = {
        "links": [
            {"link_id": "other", "d1_m": 2000.0, "d2_m": 2000.0, "h_m": -100.0,
             "frequency_mhz": 900.0},
            dict(LINK, link_id="target"),
            {"link_id": "bad", **LINK, "d2_m": -1.0},
        ]
    }
    body = client.post("/v1/diffraction/batch", json=payload).json()
    assert body["count"] == 3
    other, target, bad = body["results"]

    assert target["ok"] is True
    res = target["result"]
    assert res["link_id"] == "target"
    assert math.isclose(res["v"], V, rel_tol=REL_TOL)
    assert math.isclose(res["first_fresnel_radius_m"], R1, rel_tol=REL_TOL)
    assert math.isclose(res["clearance_fresnel_ratio"], RATIO, rel_tol=REL_TOL)
    assert math.isclose(res["loss_db"], LOSS, rel_tol=REL_TOL)

    # 同批其他链路互不影响：通视条损耗为零，非法条只在自身报错
    assert other["ok"] is True and other["result"]["loss_db"] == 0.0
    assert bad["ok"] is False and "d2_m" in bad["error"]["reason"]


def test_all_paths_identical():
    """三种调用路径对同一几何必须报同一组数。"""
    p = assess_parameters(D1, D2, H, F_MHZ)
    f = assess_full(D1, D2, H, F_MHZ)
    http = client.post("/v1/diffraction/assessment", json=LINK).json()
    assert f.v == p.v
    assert f.first_fresnel_radius_m == p.first_fresnel_radius_m
    assert f.clearance_fresnel_ratio == p.clearance_fresnel_ratio
    assert math.isclose(http["v"], f.v, rel_tol=1e-12)
    assert math.isclose(http["first_fresnel_radius_m"], f.first_fresnel_radius_m, rel_tol=1e-12)
    assert math.isclose(http["loss_db"], f.loss_db, rel_tol=1e-12)


def test_frequency_double_scales_v_by_sqrt2_on_this_geometry():
    """同一几何只把频率加倍，v 按 √2 变化、r1 按 1/√2 变化。"""
    a = assess_full(D1, D2, H, F_MHZ)
    a2 = assess_full(D1, D2, H, F_MHZ * 2.0)
    assert math.isclose(a2.v, a.v * math.sqrt(2.0), rel_tol=1e-12)
    assert math.isclose(a2.first_fresnel_radius_m, a.first_fresnel_radius_m / math.sqrt(2.0),
                        rel_tol=1e-12)


def test_d1_d2_swap_invariant():
    """约化距离对 d1/d2 对称：交换收发端，v/r1/损耗不变。"""
    a = assess_full(D1, D2, H, F_MHZ)
    swapped = assess_full(D2, D1, H, F_MHZ)
    assert math.isclose(swapped.v, a.v, rel_tol=1e-12)
    assert math.isclose(swapped.first_fresnel_radius_m, a.first_fresnel_radius_m, rel_tol=1e-12)
    assert math.isclose(swapped.loss_db, a.loss_db, rel_tol=1e-12)


def test_unrelated_asymmetric_link_also_matches_definition():
    """换另一条合法的非对称链路，仍须符合同一套定义（证明非特例硬编码）。"""
    d1, d2, h, f_mhz = 5000.0, 2000.0, 4.0, 1800.0
    lam, v, r1, ratio, loss = _expected(d1, d2, h, f_mhz)
    a = assess_full(d1, d2, h, f_mhz)
    assert math.isclose(a.v, v, rel_tol=REL_TOL)
    assert math.isclose(a.first_fresnel_radius_m, r1, rel_tol=REL_TOL)
    assert math.isclose(a.clearance_fresnel_ratio, ratio, rel_tol=REL_TOL)
    assert math.isclose(a.loss_db, loss, rel_tol=REL_TOL)
    assert math.isclose(a.wavelength_m, lam, rel_tol=REL_TOL)
