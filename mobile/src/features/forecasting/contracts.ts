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
  id: string; created_at: string; base_date: string; horizon: Horizon; method: ForecastMethod;
  model_version: string; dataset_version: string; seed: number;
  points: ForecastPoint[]; risk: ForecastRisk | null; estimate_notice: string;
}
export interface DailySeries {
  base_date: string;
  series: {date: string; income: string; expense: string; references: string[]}[];
}
