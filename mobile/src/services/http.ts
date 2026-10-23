import axios, { type AxiosRequestConfig } from 'axios';
import { env } from '@/config/env';
import { ApiError, isApiErrorBody } from './errors';
export { ApiError } from './errors';

export const http = axios.create({ baseURL: env.apiUrl, timeout: 10000, headers: { Accept: 'application/json' } });
let token: string | null = null;
let unauthorized: (() => void) | null = null;
export function setAccessToken(value: string | null) { token = value; }
export function setUnauthorizedHandler(handler: (() => void) | null) { unauthorized = handler; }
http.interceptors.request.use(config => {
  if (token) config.headers.set('Authorization', `Bearer ${token}`);
  return config;
});
http.interceptors.response.use(response => response, (error: unknown) => {
  if (!axios.isAxiosError(error)) return Promise.reject(new ApiError(null, 'UNKNOWN_ERROR', 'Não foi possível concluir a solicitação.'));
  if (error.code === 'ERR_CANCELED') return Promise.reject(new ApiError(null, 'CANCELLED', 'Solicitação cancelada.'));
  if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') return Promise.reject(new ApiError(null, 'TIMEOUT', 'A solicitação demorou demais. Tente novamente.'));
  const status = error.response?.status ?? null;
  if (status === 401 && !error.config?.url?.includes('/auth/login')) unauthorized?.();
  if (isApiErrorBody(error.response?.data)) {
    const body = error.response.data;
    return Promise.reject(new ApiError(status, body.error.code, body.error.message, body.request_id));
  }
  const message = status === null ? 'Sem conexão com a API. Verifique sua rede e o endereço configurado.' : status >= 500 ? 'O servidor está temporariamente indisponível.' : status === 422 ? 'Confira os campos informados.' : 'Não foi possível concluir a solicitação.';
  return Promise.reject(new ApiError(status, status === null ? 'NETWORK_ERROR' : `HTTP_${status}`, message));
});
export async function request<T>(path: string, options: AxiosRequestConfig = {}): Promise<T> {
  if (!path.startsWith('/') || path.startsWith('//') || path.includes('://') || path.includes('..')) throw new Error('Use um caminho relativo à API.');
  // Callers cannot override the host, Authorization header or URL through options.
  const { data } = await http.request<T>({ ...options, baseURL: env.apiUrl, url: path });
  return data;
}
