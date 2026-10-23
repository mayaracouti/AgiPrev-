import { render, screen, waitFor, fireEvent } from "@testing-library/react-native";
import { FinancialDashboard } from "@/features/forecasting/FinancialDashboard";
import { latestForecast, forecastSeries, retryForecastRefreshes } from "@/features/forecasting/api";
let mockChartProps: {dates: string[]; labels: string[]}[] = [];
jest.mock("@/auth/AuthProvider", () => ({useAuth: () => ({session: {accounts: [{id: "account"}]}})}));
jest.mock("expo-router", () => ({router: {push: jest.fn()}}));
jest.mock("@/features/forecasting/api", () => ({latestForecast: jest.fn(), forecastSeries: jest.fn(), retryForecastRefreshes: jest.fn()}));
jest.mock("@/components/ForecastChart", () => ({ForecastChart: (props: {dates: string[]; labels: string[]}) => {mockChartProps.push(props); return null;}}));
const run = {id: "run", base_date: "2026-10-23", horizon: 7, points: [{date: "2026-10-24", balance: "5.00", income: "10.00"}], risk: null};
beforeEach(() => {
  jest.resetAllMocks(); mockChartProps = [];
  jest.mocked(forecastSeries).mockResolvedValue({base_date: "2026-10-23", current_date: "2026-10-23", points: [
    {date: "2026-10-23", observed_balance: "15.00", predicted_balance: "10.00", predicted_expense: "0.00", observed_expense: "2.00"},
    {date: "2026-10-24", observed_balance: "999.00", predicted_balance: "5.00", predicted_expense: "0.00", observed_expense: null}],
    deviation: {actual_expense: "2.00", predicted_expense: "0.00", amount: "2.00", percent: null, alert_eligible: false}});
});
test("shows safe state and never draws future data as observed even if API sends it", async () => {
  jest.mocked(latestForecast).mockResolvedValue({current_balance: "15.00", stale: false, forecast: run as never});
  render(<FinancialDashboard />);
  await screen.findByText("Sem déficit previsto neste horizonte");
  expect(screen.getByText(/Desvio isolado não gera alerta/)).toBeTruthy();
  const observed = mockChartProps.find(p => p.labels.includes("Observado"));
  expect(observed?.dates).toEqual(["2026-10-23"]);
});
test("shows risk date, stale warning and experiment trace", async () => {
  jest.mocked(latestForecast).mockResolvedValue({current_balance: "15.00", stale: true, forecast: {...run, risk: {date: "2026-10-24", balance: "-5.00"}, experiment_id: "experiment-1"} as never});
  render(<FinancialDashboard />);
  await screen.findByText(/Risco de déficit em 2026-10-24/);
  expect(screen.getByText(/Previsão obsoleta/)).toBeTruthy();
  expect(screen.getByText(/Experimento experiment-1/)).toBeTruthy();
});
test("network error allows retry without fabricating a forecast", async () => {
  jest.mocked(latestForecast).mockRejectedValueOnce(new Error("offline")).mockResolvedValue({current_balance: "15.00", stale: false, forecast: null});
  render(<FinancialDashboard />);
  await screen.findByRole("alert");
  fireEvent.press(screen.getByText("Atualizar previsão e saldo"));
  await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  expect(screen.getByText(/Nenhuma previsão salva/)).toBeTruthy();
});

test("explicit recovery retries durable refresh before refetching latest", async () => {
  jest.mocked(latestForecast).mockResolvedValue({current_balance: "15.00", stale: true, forecast: run as never});
  jest.mocked(retryForecastRefreshes).mockResolvedValue([{id: "job", status: "completed", correlation_id: "correlation"}]);
  render(<FinancialDashboard />);
  fireEvent.press(await screen.findByText("Reprocessar atualização pendente"));
  await waitFor(() => expect(latestForecast).toHaveBeenCalledTimes(2));
  expect(retryForecastRefreshes).toHaveBeenCalledWith("account");
});
