import { render, screen, fireEvent } from "@testing-library/react-native";
import { AlertCenter } from "@/features/forecasting/AlertCenter";
import { alerts, alertDetail, readAlert } from "@/features/forecasting/api";
import { enableLocalNotifications } from "@/features/notifications";
jest.mock("@/auth/AuthProvider", () => ({useAuth: () => ({session: {accounts: [{id: "account"}]}})}));
jest.mock("expo-router", () => ({useLocalSearchParams: () => ({})}));
jest.mock("@/features/notifications", () => ({enableLocalNotifications: jest.fn(), notifyAlert: jest.fn(), observeNotificationOpening: () => () => {}}));
jest.mock("@/features/forecasting/api", () => ({alerts: jest.fn(), alertDetail: jest.fn(), readAlert: jest.fn()}));
const row = {id: "alert1", account_id: "account", run_id: "version1", severity: "critical", title: "Risco fictício", message: "Déficit estimado", risk_date: "2026-10-25", deficit: "10.00", recommendation: "Revise gastos até 2026-10-25", read_at: null, created_at: "2026-10-23"};
beforeEach(() => {
  jest.resetAllMocks(); jest.mocked(alerts).mockResolvedValue([row]);
  jest.mocked(alertDetail).mockResolvedValue(row);
  jest.mocked(readAlert).mockResolvedValue({...row, read_at: "2026-10-23"});
});
test("loads authorized detail and persists read state through API", async () => {
  render(<AlertCenter />);
  fireEvent.press(await screen.findByText("Detalhes do alerta alert1"));
  await screen.findByText("Revise gastos até 2026-10-25");
  fireEvent.press(screen.getByText("Marcar como lido"));
  await screen.findByText("critical · Lido");
  expect(readAlert).toHaveBeenCalledWith("account", "alert1");
  expect(enableLocalNotifications).not.toHaveBeenCalled();
});
test("denied notification permission keeps central usable", async () => {
  jest.mocked(enableLocalNotifications).mockResolvedValue(false);
  render(<AlertCenter />);
  fireEvent.press(screen.getByText("Permitir notificações locais"));
  await screen.findByText(/Permissão negada/);
  expect(screen.queryByText("Notificar neste dispositivo")).toBeNull();
  expect(await screen.findByText("Risco fictício")).toBeTruthy();
});
