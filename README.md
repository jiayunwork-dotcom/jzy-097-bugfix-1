# 刃形绕射损耗计算服务

无线传播评估组内部使用的单刃障碍绕射内核，仅经 HTTP 提供。根据链路几何与频率计算菲涅尔–基尔霍夫参数、余隙、第一菲涅尔区半径与附加损耗。不做自由空间链路预算，与光学缝衍射无关。

## 定义与约定

- 几何：`d1_m`、`d2_m` 为障碍到发/收端的水平距离（m，必须为正）；`h_m` 为障碍相对收发直视线的超出高度（m），**遮挡为正、低于直视线为负**。
- 频率：`frequency_mhz`（MHz，必须为正），波长 λ = c / f。
- 菲涅尔参数：`v = h·√(2·(d1+d2) / (λ·d1·d2))`。
- 第一菲涅尔区半径（障碍截面）：`r1 = √(λ·d1·d2/(d1+d2))`；余隙 = −h。
- 附加损耗（ITU-R P.526 单刃近似，标准库手写）：
  - `v ≤ −0.78`：0 dB（余隙充足时不硬加损耗）；
  - `v > −0.78`：`6.9 + 20·log10(√((v−0.1)²+1) + v − 0.1)`。
  - 擦边 `v=0` 时约 6.0 dB；v 增大损耗单调升高。
- 通视判定：`v < 0`（障碍顶部低于直视线）为通视。

## 模块划分

| 文件 | 职责 |
| --- | --- |
| `app/geometry.py` | 链路几何与余隙 |
| `app/fresnel.py` | 菲涅尔–基尔霍夫参数 v、波长换算 |
| `app/zone.py` | 第一菲涅尔区半径 |
| `app/loss.py` | 附加损耗近似 |
| `app/validation.py` | 输入校验（带原因拒绝） |
| `app/service.py` | 评估编排 |
| `app/batch.py` | 批量调度（逐条独立、错误隔离） |
| `app/presets.py` | 预置算例（山脊略微遮挡，损耗 > 6 dB） |
| `app/schemas.py` | 接口数据模型 |
| `app/main.py` | FastAPI 接口层 |

## 接口

- `POST /v1/diffraction/parameters` — 输入几何与频率，返回 `v`、`clearance_m`、`clearance_fresnel_ratio`、`first_fresnel_radius_m`、`wavelength_m`。
- `POST /v1/diffraction/assessment` — 同样输入，追加 `loss_db` 与 `is_los`。
- `POST /v1/diffraction/batch` — `{"links": [...]}` 一批链路一次算完，各条结果独立，单条不合法只在该条返回错误。
- `GET /v1/examples/ridge` — 预置的山脊略微遮挡算例（损耗 ≈ 10 dB > 6 dB）。
- `GET /healthz` — 存活探针。

输入不合法（距离/频率非正、非有限数）返回 `400` 与带原因的错误 JSON：

```json
{"error": {"code": "INVALID_INPUT", "reason": "d1_m 必须为正数，收到 0.0"}}
```

## 本地运行

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
pytest
```

## Docker

```bash
docker build -t knife-edge-diffraction .
docker run --rm -p 8080:8080 knife-edge-diffraction      # 服务挂在固定端口 8080
docker run --rm knife-edge-diffraction pytest            # 在容器内执行测试
```

## 测试重点

`tests/` 用自动化测试钉住以下关系：

- 擦边 `h=0`：`v=0`，附加损耗约 6 dB；
- 只加高障碍：损耗随之升高；
- 只把频率加倍：同一几何下 `v` 变为原来的 √2 倍；
- `d1=d2` 且障碍显著低于直视线：损耗趋零、判定通视；
- 批量调用各条独立、互不覆盖；非法输入返回带原因的错误 JSON。
