"""批量调度：把一批链路几何作为一组一次算完。

每条链路独立评估、互不覆盖：单条输入不合法只在该条的结果里
携带错误，不影响同批其他链路。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from .service import FullAssessment, assess_full
from .validation import ValidationError


@dataclass(frozen=True)
class BatchItem:
    """批量请求中的一条链路。"""

    link_id: Optional[str]
    d1_m: float
    d2_m: float
    h_m: float
    frequency_mhz: float


@dataclass(frozen=True)
class BatchItemResult:
    """单条链路的评估结果：成功带 result，失败带 error_reason。"""

    link_id: Optional[str]
    ok: bool
    result: Optional[FullAssessment] = None
    error_reason: Optional[str] = None


def evaluate_batch(
    items: Iterable[BatchItem],
    assess: Callable[[float, float, float, float], FullAssessment] = assess_full,
) -> list[BatchItemResult]:
    """逐条调度评估，结果与输入一一对应、顺序保持一致。"""
    results: list[BatchItemResult] = []
    for item in items:
        try:
            assessment = assess(item.d1_m, item.d2_m, item.h_m, item.frequency_mhz)
        except ValidationError as exc:
            results.append(
                BatchItemResult(link_id=item.link_id, ok=False, error_reason=exc.reason)
            )
        else:
            results.append(
                BatchItemResult(link_id=item.link_id, ok=True, result=assessment)
            )
    return results
