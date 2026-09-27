"""预置算例：山脊略微遮挡的链路。

d1=3 km，d2=4 km，障碍高出直视线 8 m，900 MHz。
该几何下 v ≈ 0.47，附加损耗 ≈ 10 dB，大于 6 dB。
"""

from __future__ import annotations

from .batch import BatchItem

RIDGE_LINK_ID = "preset-ridge-slight-obstruction"

RIDGE_PRESET = BatchItem(
    link_id=RIDGE_LINK_ID,
    d1_m=3000.0,
    d2_m=4000.0,
    h_m=8.0,
    frequency_mhz=900.0,
)
