"""刃形绕射附加损耗近似（ITU-R P.526 单刃绕射项）。

    v <= -0.78 :  J(v) = 0 dB            （余隙充足，不再硬加损耗）
    v >  -0.78 :  J(v) = 6.9 + 20*log10(sqrt((v-0.1)^2 + 1) + v - 0.1)

性质：
- v = 0（障碍恰好擦着直视线）时 J ≈ 6.0 dB；
- v 增大（障碍加高）损耗单调升高；
- v 足够负（深度通视）时损耗恒为 0 dB。

注意：这里只算绕射引起的附加损耗，绝不套用自由空间路径损耗来冒充。
"""

from __future__ import annotations

import math

# 近似式适用下界，约 -0.8；低于该值认为余隙充足，附加损耗为零
V_CLEARANCE_THRESHOLD = -0.78


def knife_edge_loss_db(v: float) -> float:
    """由菲涅尔参数 v 估算刃形绕射附加损耗（dB）。"""
    if v <= V_CLEARANCE_THRESHOLD:
        return 0.0
    shifted = v - 0.1
    return 6.9 + 20.0 * math.log10(math.sqrt(shifted * shifted + 1.0) + shifted)
