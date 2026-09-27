"""批量调度测试：各条链路独立、互不覆盖。"""

from app.batch import BatchItem, evaluate_batch
from app.service import assess_full


def _item(link_id, h_m, freq=900.0, d1=3000.0, d2=4000.0):
    return BatchItem(link_id=link_id, d1_m=d1, d2_m=d2, h_m=h_m, frequency_mhz=freq)


def test_batch_results_match_individual_evaluation():
    items = [_item("a", 8.0), _item("b", -50.0), _item("c", 0.0, freq=1800.0)]
    results = evaluate_batch(items)
    assert [r.link_id for r in results] == ["a", "b", "c"]
    assert all(r.ok for r in results)
    for item, r in zip(items, results):
        solo = assess_full(item.d1_m, item.d2_m, item.h_m, item.frequency_mhz)
        assert r.result == solo


def test_batch_isolates_invalid_items():
    """一条不合法只影响自己，其他链路照常出结果。"""
    items = [
        _item("ok-1", 8.0),
        BatchItem(link_id="bad", d1_m=0.0, d2_m=4000.0, h_m=8.0, frequency_mhz=900.0),
        _item("ok-2", -30.0),
    ]
    results = evaluate_batch(items)
    assert [r.ok for r in results] == [True, False, True]
    bad = results[1]
    assert bad.link_id == "bad"
    assert bad.error_reason and "d1_m" in bad.error_reason
    assert results[2].result is not None and results[2].result.loss_db == 0.0


def test_batch_does_not_leak_state_between_items():
    """相同几何重复出现，结果一致，互不覆盖。"""
    items = [_item("x", 8.0), _item("y", 8.0)]
    results = evaluate_batch(items)
    assert results[0].result == results[1].result
    assert results[0].link_id != results[1].link_id
