export type ErrorCode = 'NETWORK_ERROR' | 'TIMEOUT' | 'CANCELLED' | 'INVALID_RESPONSE' | string;
export interface ApiErrorBody { error: { code: string; message: string; details: { field: string; code: string }[] }; request_id: string; }
export class ApiError extends Error {
  constructor(public readonly status: number | null, public readonly code: ErrorCode, message: string, public readonly requestId?: string) {
    super(message);
    this.name = 'ApiError';
  }
}
export function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Não foi possível concluir a solicitação. Tente novamente.';
}
export function isApiErrorBody(value: unknown): value is ApiErrorBody {
  if (typeof value !== 'object' || value === null || !('error' in value)) return false;
  const error = value.error;
  return typeof error === 'object' && error !== null && 'code' in error && typeof error.code === 'string' && 'message' in error && typeof error.message === 'string';
}
