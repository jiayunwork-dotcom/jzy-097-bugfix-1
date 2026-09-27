"""接口数据模型（Pydantic）。"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LinkInput(BaseModel):
    """单条链路输入。距离 m，频率 MHz，h 遮挡为正。"""

    model_config = ConfigDict(extra="forbid")

    link_id: Optional[str] = None
    d1_m: float = Field(description="障碍到发射端的水平距离，m")
    d2_m: float = Field(description="障碍到接收端的水平距离，m")
    h_m: float = Field(description="障碍相对直视线的超出高度，m；遮挡为正")
    frequency_mhz: float = Field(description="频率，MHz")


class BatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    links: list[LinkInput] = Field(min_length=1, max_length=1000)


class ParameterAssessmentResponse(BaseModel):
    link_id: Optional[str]
    v: float
    clearance_m: float
    clearance_fresnel_ratio: float
    first_fresnel_radius_m: float
    wavelength_m: float


class FullAssessmentResponse(ParameterAssessmentResponse):
    loss_db: float
    is_los: bool


class ErrorBody(BaseModel):
    code: str
    reason: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class BatchItemResponse(BaseModel):
    link_id: Optional[str]
    ok: bool
    result: Optional[FullAssessmentResponse] = None
    error: Optional[ErrorBody] = None


class BatchResponse(BaseModel):
    count: int
    results: list[BatchItemResponse]
