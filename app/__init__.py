"""刃形绕射损耗计算服务。

仅实现单刃障碍的绕射内核，经 HTTP 暴露。
模块划分：
- geometry    链路几何与余隙
- fresnel     菲涅尔-基尔霍夫参数 v
- zone        第一菲涅尔区半径
- loss        附加损耗近似（ITU-R P.526 刃形绕射）
- validation  输入校验
- service     评估编排
- batch       批量调度
- presets     预置算例
- schemas     接口数据模型
- main        FastAPI 接口层
"""
