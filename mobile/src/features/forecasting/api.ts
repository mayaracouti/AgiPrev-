import { request } from "@/services/http";
import type { DailySeries, ForecastMethod, ForecastRun, Horizon } from "./contracts";
export const dailySeries = (account: string) => request<DailySeries>(`/accounts/${account}/daily-series`);
export const forecasts = (account: string) => request<ForecastRun[]>(`/accounts/${account}/forecasts`);
export const forecast = (account: string, horizon: Horizon, method: ForecastMethod) =>
  request<ForecastRun>(`/accounts/${account}/forecasts`, {method: "POST", data: {horizon, method}});
