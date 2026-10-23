from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    field: str
    code: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorBody
    request_id: str


ERROR_RESPONSES = {status: {"model": ErrorResponse} for status in (401, 403, 404, 422, 500, 503)}
