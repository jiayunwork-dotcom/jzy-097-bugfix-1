"""链路几何与余隙。

几何约定（钉死，不得翻转）：
- h 为障碍顶部相对收发直视线的超出高度，单位 m。
  障碍高出直视线为正（遮挡），低于直视线为负（有余隙）。
- d1、d2 分别为障碍到发射端、接收端的水平距离，单位 m，必须为正。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LinkGeometry:
    """单刃障碍链路几何。"""

    d1_m: float  # 障碍到发射端的水平距离
    d2_m: float  # 障碍到接收端的水平距离
    h_m: float  # 障碍相对直视线的超出高度：遮挡为正，余隙为负

    @property
    def total_distance_m(self) -> float:
        """收发间水平总距离。"""
        return self.d1_m + self.d2_m

    @property
    def reduced_distance_m(self) -> float:
        """障碍截面处的约化距离（m）。

        菲涅尔参数与第一区半径都只经由这一项依赖 d1、d2，
        按障碍在全程中的位置比例展开，避免长链路下 d1·d2 直接相乘：
        d1·d2/(d1+d2) = d1·(d2/(d1+d2))。
        """
        return self.d1_m * (self.d2_m / self.total_distance_m)

    @property
    def clearance_m(self) -> float:
        """余隙：直视线高出障碍顶部的高度。

        与 h 符号相反：余隙为正表示直视线越过障碍（通视方向），
        余隙为负表示障碍挡住直视线。
        """
        return -self.h_m
