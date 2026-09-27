"""附加损耗近似的关键性质测试。"""

from app.loss import knife_edge_loss_db


def test_grazing_loss_is_about_six_db():
    """v=0（擦边）时附加损耗约 6 dB。"""
    loss = knife_edge_loss_db(0.0)
    assert 5.9 < loss < 6.2


def test_deep_clearance_loss_tends_to_zero():
    """v 足够负（深度通视）时附加损耗为零，不硬加 6 dB。"""
    assert knife_edge_loss_db(-0.78) == 0.0
    assert knife_edge_loss_db(-1.5) == 0.0
    assert knife_edge_loss_db(-8.0) == 0.0


def test_loss_increases_with_v():
    """障碍加高（v 增大）损耗随之升高。"""
    losses = [knife_edge_loss_db(v) for v in (0.0, 0.5, 1.0, 2.0, 4.0)]
    assert all(b > a for a, b in zip(losses, losses[1:]))


def test_loss_just_above_threshold_is_small():
    """阈值附近损耗接近零且非负（v=-0.75 时约 0.2 dB）。"""
    loss = knife_edge_loss_db(-0.75)
    assert 0.0 <= loss < 0.3
