from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        self.status = status
        self.code = code
        self.message = message


def install_error_handlers(app: FastAPI) -> None:
    def response(request: Request, status: int, code: str, message: str, details=None):
        return JSONResponse(
            status_code=status,
            content={
                "error": {"code": code, "message": message, "details": details or []},
                "request_id": getattr(request.state, "request_id", str(uuid4())),
            },
            headers={"WWW-Authenticate": "Bearer"} if status == 401 else None,
        )

    @app.middleware("http")
    async def identify_request(request: Request, call_next):
        request.state.request_id = str(uuid4())
        result = await call_next(request)
        result.headers["X-Request-ID"] = request.state.request_id
        return result

    @app.exception_handler(AppError)
    async def domain_error(request: Request, exc: AppError):
        return response(request, exc.status, exc.code, exc.message)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: HTTPException):
        messages = {
            401: "Sessão inválida ou expirada.",
            403: "Acesso não permitido.",
            404: "Recurso não encontrado.",
            405: "Método não permitido.",
            503: "Serviço temporariamente indisponível.",
        }
        return response(
            request,
            exc.status_code,
            f"HTTP_{exc.status_code}",
            messages.get(exc.status_code, "Não foi possível concluir a solicitação."),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Never echo submitted passwords, tokens, URLs or raw inputs in error responses.
        details = [
            {"field": ".".join(str(part) for part in item["loc"]), "code": item["type"]}
            for item in exc.errors()
        ]
        return response(request, 422, "VALIDATION_ERROR", "Confira os campos informados.", details)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        return response(request, 503, "DATABASE_UNAVAILABLE", "Banco de dados indisponível.")

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        return response(request, 500, "INTERNAL_ERROR", "Ocorreu um erro no servidor.")
