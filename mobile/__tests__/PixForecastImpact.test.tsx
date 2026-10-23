import { render, screen } from "@testing-library/react-native";
import { PixForecastImpact } from "@/features/forecasting/PixForecastImpact";
import { forecastRun } from "@/features/forecasting/api";
jest.mock("@/features/forecasting/api", () => ({forecastRun: jest.fn()}));
jest.mock("@/components/ForecastChart", () => ({ForecastChart: () => null}));
test("retrieves immutable versions and calculates monetary difference on matching dates", async () => {
  jest.mocked(forecastRun).mockImplementation(async (_account, id) => ({points: id === "old" ? [{date: "2026-10-25", balance: "10.02"}, {date: "2026-10-26", balance: "5.00"}] : [{date: "2026-10-25", balance: "-5.01"}]} as never));
  render(<PixForecastImpact account="account" before="old" after="new" />);
  await screen.findByText(/Diferença em 2026-10-25: −R\$ 15,03/);
  expect(forecastRun).toHaveBeenCalledWith("account", "old");
  expect(forecastRun).toHaveBeenCalledWith("account", "new");
});
