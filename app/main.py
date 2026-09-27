"""FastAPI 接口层。

两类调用：
- POST /v1/diffraction/parameters  返回 v、余隙、第一菲涅尔区半径
- POST /v1/diffraction/assessment  同样输入，追加附加损耗与通视判定
另加：
- POST /v1/diffraction/batch       一批链路一次算完，各条独立
- GET  /v1/examples/ridge          预置的山脊略微遮挡算例（损耗 > 6 dB）
- GET  /healthz                    存活探针
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .batch import BatchItem, evaluate_batch
from .presets import RIDGE_PRESET
from .schemas import (
    BatchItemResponse,
    BatchRequest,
    BatchResponse,
    ErrorBody,
    ErrorResponse,
    FullAssessmentResponse,
    LinkInput,
    ParameterAssessmentResponse,
)
from .service import FullAssessment, ParameterAssessment, assess_full, assess_parameters
from .validation import ValidationError

app = FastAPI(
    title="Knife-Edge Diffraction Service",
    version="1.0.0",
    description="单刃障碍绕射内核：菲涅尔参数、余隙、第一菲涅尔区半径与附加损耗。",
)


@app.exception_handler(ValidationError)
async def validation_error_handler(_: Request, exc: ValidationError) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code="INVALID_INPUT", reason=exc.reason))
    return JSONResponse(status_code=400, content=body.model_dump())


def _to_parameter_response(
    link_id: str | None, a: ParameterAssessment
) -> ParameterAssessmentResponse:
    return ParameterAssessmentResponse(
        link_id=link_id,
        v=a.v,
        clearance_m=a.clearance_m,
        clearance_fresnel_ratio=a.clearance_fresnel_ratio,
        first_fresnel_radius_m=a.first_fresnel_radius_m,
        wavelength_m=a.wavelength_m,
    )


def _to_full_response(link_id: str | None, a: FullAssessment) -> FullAssessmentResponse:
    return FullAssessmentResponse(
        link_id=link_id,
        v=a.v,
        clearance_m=a.clearance_m,
        clearance_fresnel_ratio=a.clearance_fresnel_ratio,
        first_fresnel_radius_m=a.first_fresnel_radius_m,
        wavelength_m=a.wavelength_m,
        loss_db=a.loss_db,
        is_los=a.is_los,
    )


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post(
    "/v1/diffraction/parameters",
    response_model=ParameterAssessmentResponse,
    responses={400: {"model": ErrorResponse}},
)
def diffraction_parameters(link: LinkInput) -> ParameterAssessmentResponse:
    """第一类调用：返回 v、余隙与第一菲涅尔区半径。"""
    a = assess_parameters(link.d1_m, link.d2_m, link.h_m, link.frequency_mhz)
    return _to_parameter_response(link.link_id, a)


@app.post(
    "/v1/diffraction/assessment",
    response_model=FullAssessmentResponse,
    responses={400: {"model": ErrorResponse}},
)
def diffraction_assessment(link: LinkInput) -> FullAssessmentResponse:
    """第二类调用：追加附加损耗与是否通视的判定。"""
    a = assess_full(link.d1_m, link.d2_m, link.h_m, link.frequency_mhz)
    return _to_full_response(link.link_id, a)


@app.post(
    "/v1/diffraction/batch",
    response_model=BatchResponse,
    responses={400: {"model": ErrorResponse}},
)
def diffraction_batch(request: BatchRequest) -> BatchResponse:
    """批量调用：各条链路独立评估，单条失败不影响其他。"""
    items = [
        BatchItem(
            link_id=link.link_id,
            d1_m=link.d1_m,
            d2_m=link.d2_m,
            h_m=link.h_m,
            frequency_mhz=link.frequency_mhz,
        )
        for link in request.links
    ]
    results = evaluate_batch(items)
    return BatchResponse(
        count=len(results),
        results=[
            BatchItemResponse(
                link_id=r.link_id,
                ok=r.ok,
                result=_to_full_response(r.link_id, r.result) if r.ok else None,
                error=None
                if r.ok
                else ErrorBody(code="INVALID_INPUT", reason=r.error_reason or ""),
            )
            for r in results
        ],
    )


@app.get(
    "/v1/examples/ridge",
    response_model=FullAssessmentResponse,
)
def ridge_example() -> FullAssessmentResponse:
    """预置算例：山脊略微遮挡，附加损耗大于 6 dB。"""
    p = RIDGE_PRESET
    a = assess_full(p.d1_m, p.d2_m, p.h_m, p.frequency_mhz)
    return _to_full_response(p.link_id, a)
