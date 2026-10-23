import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";
import { PersistedForecast } from "@/features/forecasting/PersistedForecast";
import { dailySeries, forecast, forecasts } from "@/features/forecasting/api";

jest.mock("@/auth/AuthProvider", () => ({useAuth: () => ({session: {accounts: [{id: "account"}]}})}));
jest.mock("@/features/forecasting/api", () => ({dailySeries: jest.fn(), forecast: jest.fn(), forecasts: jest.fn()}));
jest.mock("@/components/ForecastChart", () => ({ForecastChart: () => null}));

beforeEach(() => jest.resetAllMocks());

test("generates API forecast and shows version and recurring calendar", async () => {
  const run = {id: "version-1", base_date: "2026-10-23", horizon: 7, model_version: "boosted-stumps-v1",
    points: [{date: "2026-10-24", balance: "10.01", variable_expense: "1.00", events: [
      {date: "2026-10-24", direction: "credit", amount: "1000.00", description: "Salário fictício"}]}]};
  jest.mocked(dailySeries).mockResolvedValue({base_date: "2026-10-23", series: []});
  jest.mocked(forecast).mockResolvedValue(run as Awaited<ReturnType<typeof forecast>>);
  jest.mocked(forecasts).mockResolvedValue([run as Awaited<ReturnType<typeof forecast>>]);
  render(<PersistedForecast />);
  fireEvent.press(screen.getByText("Gerar previsão pela API"));
  await waitFor(() => expect(screen.getByText(/Salário fictício/)).toBeTruthy());
  expect(forecast).toHaveBeenCalledWith("account", 7, "hybrid");
  expect(screen.getByText(/Data-base 2026-10-23/)).toBeTruthy();
});

test("API failure shows error and does not invent a forecast", async () => {
  jest.mocked(dailySeries).mockRejectedValue(new Error("offline"));
  render(<PersistedForecast />);
  fireEvent.press(screen.getByText("Gerar previsão pela API"));
  await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
  expect(forecast).not.toHaveBeenCalled();
  expect(screen.queryByText("Calendário previsto")).toBeNull();
});
