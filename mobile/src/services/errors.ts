export type ErrorCode =
  | "NETWORK_ERROR"
  | "TIMEOUT"
  | "CANCELLED"
  | "INVALID_RESPONSE"
  | string;
export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: { field: string; code: string }[];
  };
  request_id: string;
}
export class ApiError extends Error {
  constructor(
    public readonly status: number | null,
    public readonly code: ErrorCode,
    message: string,
    public readonly requestId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
export function errorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : "Não foi possível concluir a solicitação. Tente novamente.";
}
export function isApiErrorBody(value: unknown): value is ApiErrorBody {
  if (typeof value !== "object" || value === null || !("error" in value))
    return false;
  const error = value.error;
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    typeof error.code === "string" &&
    "message" in error &&
    typeof error.message === "string"
  );
}

export function normalizeHttpError(
  code: string | undefined,
  status: number | null,
  data: unknown,
): ApiError {
  if (code === "ERR_CANCELED")
    return new ApiError(null, "CANCELLED", "Solicitação cancelada.");
  if (code === "ECONNABORTED" || code === "ETIMEDOUT")
    return new ApiError(
      null,
      "TIMEOUT",
      "A solicitação demorou demais. Tente novamente.",
    );
  if (isApiErrorBody(data))
    return new ApiError(
      status,
      data.error.code,
      data.error.message,
      data.request_id,
    );
  const message =
    status === null
      ? "Sem conexão com a API. Verifique sua rede e o endereço configurado."
      : status >= 500
        ? "O servidor está temporariamente indisponível."
        : status === 422
          ? "Confira os campos informados."
          : "Não foi possível concluir a solicitação.";
  return new ApiError(
    status,
    status === null ? "NETWORK_ERROR" : `HTTP_${status}`,
    message,
  );
}
