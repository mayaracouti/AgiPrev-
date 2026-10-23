export type ForecastMethod = "hybrid" | "constant" | "moving_average" | "seasonal";
export type Horizon = 7 | 15 | 30;
export interface ForecastRisk { date: string; balance: string }
export interface ForecastEvent {
  date: string; description: string; amount: string; direction: "credit" | "debit";
  uncertainty: "uncalibrated";
}
export interface ForecastPoint {
  date: string; income: string; expense: string; fixed_expense: string;
  variable_expense: string; balance: string; events: ForecastEvent[];
}
export interface ForecastRun {
  experiment_id?: string | null; experiment_version?: string | null;
  id: string; created_at: string; base_date: string; horizon: Horizon; method: ForecastMethod;
  model_version: string; dataset_version: string; seed: number;
  points: ForecastPoint[]; risk: ForecastRisk | null; estimate_notice: string;
}
export interface DailySeries {
  base_date: string;
  series: {date: string; income: string; expense: string; references: string[]}[];
}
export interface LatestForecast {forecast: ForecastRun | null; current_balance: string; stale: boolean}
export interface ForecastSeries {
  base_date: string; current_date: string;
  points: {date: string; observed_balance: string | null; predicted_balance: string; observed_expense: string | null; predicted_expense: string}[];
  deviation: {actual_expense: string; predicted_expense: string; amount: string; percent: string | null; alert_eligible: boolean};
}
export interface PreventiveAlert {
  id: string; account_id: string; run_id: string; severity: string; title: string; message: string;
  risk_date: string; deficit: string; recommendation: string; read_at: string | null; created_at: string;
}
