import { fireEvent, render, screen } from "@testing-library/react-native";
import { ApiSimulator } from "@/features/forecasting/ApiSimulator";
import { simulateForecast } from "@/features/forecasting/api";
jest.mock("@/auth/AuthProvider", () => ({useAuth: () => ({session: {accounts: [{id: "account"}]}})}));
jest.mock("@/features/forecasting/api", () => ({simulateForecast: jest.fn()}));
jest.mock("@/components/ForecastChart", () => ({ForecastChart: () => null}));
beforeEach(() => jest.resetAllMocks());
test("rejects invalid value and sends valid hypothesis to API only", async () => {
  jest.mocked(simulateForecast).mockResolvedValue({amount: "10.00", before: {points: [{date: "2026-10-24", balance: "20.00"}]}, after: {base_date: "2026-10-23", horizon: 7, risk: null, points: [{date: "2026-10-24", balance: "10.00"}]}} as never);
  render(<ApiSimulator />);
  fireEvent.press(screen.getByText("Calcular impacto pela API"));
  expect(simulateForecast).not.toHaveBeenCalled();
  fireEvent.changeText(screen.getByLabelText("Gasto hipotético pela API"), "10,00");
  fireEvent.press(screen.getByText("Calcular impacto pela API"));
  await screen.findByText(/Impacto hipotético/);
  expect(simulateForecast).toHaveBeenCalledWith("account", "10.00", 7);
  expect(screen.getByText(/saldo real e o extrato permanecem inalterados/)).toBeTruthy();
});
