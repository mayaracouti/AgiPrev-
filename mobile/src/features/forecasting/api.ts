import { request } from "@/services/http";
import type { DailySeries, ForecastMethod, ForecastRun, Horizon } from "./contracts";
export const dailySeries = (account: string) => request<DailySeries>(`/accounts/${account}/daily-series`);
export const forecasts = (account: string) => request<ForecastRun[]>(`/accounts/${account}/forecasts`);
export const forecast = (account: string, horizon: Horizon, method: ForecastMethod) =>
  request<ForecastRun>(`/accounts/${account}/forecasts`, {method: "POST", data: {horizon, method}});
export const latestForecast = (account: string) => request<import("./contracts").LatestForecast>(`/accounts/${account}/forecasts/latest`);
export const forecastSeries = (account: string, run: string) => request<import("./contracts").ForecastSeries>(`/accounts/${account}/forecasts/${run}/series`);
export const simulateForecast = (account: string, amount: string, horizon: Horizon) => request<{before: ForecastRun; after: ForecastRun; amount: string}>(`/accounts/${account}/forecasts/simulate`, {method: "POST", data: {amount, horizon}});
export const alerts = (account: string) => request<import("./contracts").PreventiveAlert[]>(`/accounts/${account}/alerts`);
export const alertDetail = (account: string, id: string) => request<import("./contracts").PreventiveAlert>(`/accounts/${account}/alerts/${id}`);
export const readAlert = (account: string, id: string) => request<import("./contracts").PreventiveAlert>(`/accounts/${account}/alerts/${id}`, {method: "PATCH", data: {read: true}});
export const forecastRun = (account: string, run: string) => request<ForecastRun>(`/accounts/${account}/forecasts/${run}`);
export const retryForecastRefreshes = (account: string) => request<{id: string; status: string; correlation_id: string}[]>(`/accounts/${account}/forecast-refreshes/retry`, {method: "POST"});
