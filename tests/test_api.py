"""HTTP 接口层测试。"""

import math

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

BASE_LINK = {"d1_m": 3000.0, "d2_m": 4000.0, "h_m": 8.0, "frequency_mhz": 900.0}


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_parameters_endpoint_returns_v_clearance_radius():
    r = client.post("/v1/diffraction/parameters", json=BASE_LINK)
    assert r.status_code == 200
    body = r.json()
    assert body["v"] > 0.0
    assert body["clearance_m"] == -8.0
    assert body["first_fresnel_radius_m"] > 0.0
    # 该接口不附带损耗字段
    assert "loss_db" not in body


def test_assessment_endpoint_adds_loss_and_los():
    r = client.post("/v1/diffraction/assessment", json=BASE_LINK)
    assert r.status_code == 200
    body = r.json()
    assert body["loss_db"] > 6.0
    assert body["is_los"] is False


def test_grazing_link_loss_about_six_db():
    link = dict(BASE_LINK, h_m=0.0)
    body = client.post("/v1/diffraction/assessment", json=link).json()
    assert body["v"] == 0.0
    assert 5.9 < body["loss_db"] < 6.2


def test_deep_clearance_link_loss_zero_and_los():
    link = {"d1_m": 2000.0, "d2_m": 2000.0, "h_m": -100.0, "frequency_mhz": 900.0}
    body = client.post("/v1/diffraction/assessment", json=link).json()
    assert body["loss_db"] == 0.0
    assert body["is_los"] is True
    assert body["clearance_m"] == 100.0


def test_raising_obstacle_raises_loss():
    low = client.post(
        "/v1/diffraction/assessment", json=dict(BASE_LINK, h_m=4.0)
    ).json()
    high = client.post(
        "/v1/diffraction/assessment", json=dict(BASE_LINK, h_m=16.0)
    ).json()
    assert high["loss_db"] > low["loss_db"]


def test_doubling_frequency_scales_v_by_sqrt2():
    v1 = client.post(
        "/v1/diffraction/parameters", json=dict(BASE_LINK, frequency_mhz=450.0)
    ).json()["v"]
    v2 = client.post(
        "/v1/diffraction/parameters", json=dict(BASE_LINK, frequency_mhz=900.0)
    ).json()["v"]
    assert math.isclose(v2 / v1, math.sqrt(2.0), rel_tol=1e-9)


def test_non_positive_distance_rejected_with_reason():
    r = client.post("/v1/diffraction/assessment", json=dict(BASE_LINK, d1_m=0.0))
    assert r.status_code == 400
    err = r.json()["error"]
    assert err["code"] == "INVALID_INPUT"
    assert "d1_m" in err["reason"]


def test_non_positive_frequency_rejected_with_reason():
    r = client.post("/v1/diffraction/parameters", json=dict(BASE_LINK, frequency_mhz=-1.0))
    assert r.status_code == 400
    err = r.json()["error"]
    assert err["code"] == "INVALID_INPUT"
    assert "frequency_mhz" in err["reason"]


def test_ridge_preset_loss_above_six_db():
    r = client.get("/v1/examples/ridge")
    assert r.status_code == 200
    body = r.json()
    assert body["loss_db"] > 6.0
    assert body["is_los"] is False


def test_batch_endpoint_independent_results():
    payload = {
        "links": [
            dict(BASE_LINK, link_id="ok-a"),
            dict(BASE_LINK, link_id="bad", d2_m=-5.0),
            dict(BASE_LINK, link_id="ok-b", h_m=-100.0, d1_m=2000.0, d2_m=2000.0),
        ]
    }
    r = client.post("/v1/diffraction/batch", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 3
    a, bad, b = body["results"]
    assert a["ok"] and a["result"]["loss_db"] > 6.0
    assert not bad["ok"] and "d2_m" in bad["error"]["reason"]
    assert b["ok"] and b["result"]["loss_db"] == 0.0 and b["result"]["is_los"] is True
