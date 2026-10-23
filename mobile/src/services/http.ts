import { create, isAxiosError, type AxiosRequestConfig } from "axios";
import { env } from "@/config/env";
import { ApiError, normalizeHttpError } from "./errors";
export { ApiError } from "./errors";

export const http = create({
  baseURL: env.apiUrl,
  timeout: 10000,
  headers: { Accept: "application/json" },
});
let token: string | null = null;
let unauthorized: (() => void) | null = null;
export function setAccessToken(value: string | null) {
  token = value;
}
export function setUnauthorizedHandler(handler: (() => void) | null) {
  unauthorized = handler;
}
http.interceptors.request.use((config) => {
  if (token) config.headers.set("Authorization", `Bearer ${token}`);
  return config;
});
http.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (!isAxiosError(error))
      return Promise.reject(
        new ApiError(
          null,
          "UNKNOWN_ERROR",
          "Não foi possível concluir a solicitação.",
        ),
      );
    const status = error.response?.status ?? null;
    if (status === 401 && !error.config?.url?.includes("/auth/login"))
      unauthorized?.();
    return Promise.reject(
      normalizeHttpError(error.code, status, error.response?.data),
    );
  },
);
export async function request<T>(
  path: string,
  options: AxiosRequestConfig = {},
): Promise<T> {
  if (
    !path.startsWith("/") ||
    path.startsWith("//") ||
    path.includes("://") ||
    path.includes("..")
  )
    throw new Error("Use um caminho relativo à API.");
  // Callers cannot override the host, Authorization header or URL through options.
  const { data } = await http.request<T>({
    ...options,
    baseURL: env.apiUrl,
    url: path,
  });
  return data;
}
