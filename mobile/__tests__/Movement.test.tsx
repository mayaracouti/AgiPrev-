import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";
import Movement from "@/app/movement";
import { request } from "@/services/http";
import { ApiError } from "@/services/errors";

jest.mock("expo-router", () => ({useLocalSearchParams: () => ({kind: "pix"}), router: {replace: jest.fn(), canGoBack: () => false}}));
jest.mock("react-native-safe-area-context", () => require("react-native-safe-area-context/jest/mock").default);
jest.mock("@/auth/AuthProvider", () => ({useAuth: () => ({session: {accounts: [{id: "account-test"}]}})}));
jest.mock("@/features/banking/useBalance", () => ({useBalance: () => ({data: {balance: "100.00"}, loading: false})}));
jest.mock("@/features/banking/useCategories", () => ({useCategories: () => ({categories: [{id: "pix", name: "Pix"}]})}));
jest.mock("@/services/http", () => ({request: jest.fn()}));

const response = {transaction: {id: "transaction-test", amount: "10.29", description: "Compra fictícia", recipient: "loja@demo.local", occurred_on: "2026-10-23"}, balance: "89.71", simulated: true};
function fill() {
  render(<Movement />);
  fireEvent.changeText(screen.getByLabelText("Descrição"), "Compra fictícia");
  fireEvent.changeText(screen.getByLabelText("Valor em reais"), "10,29");
  fireEvent.changeText(screen.getByLabelText("Favorecido fictício"), "loja@demo.local");
  fireEvent.press(screen.getByText("Revisar movimentação"));
}
beforeEach(() => jest.mocked(request).mockReset());
test("Pix review does not send; confirmation renders server receipt", async () => {
  jest.mocked(request).mockResolvedValue(response);
  fill();
  expect(request).not.toHaveBeenCalled();
  fireEvent.press(screen.getByText("Confirmar"));
  await waitFor(() => expect(screen.getByText("Comprovante simulado")).toBeTruthy());
  expect(request).toHaveBeenCalledTimes(1);
  expect(request).toHaveBeenCalledWith("/pix/simulate", expect.objectContaining({method: "POST", data: expect.objectContaining({amount: "10.29", account_id: "account-test", recipient: "loja@demo.local"})}));
  expect(screen.getByText("Identificador: transaction-test")).toBeTruthy();
});
test("network retry retains the idempotency key and cannot silently confirm", async () => {
  jest.mocked(request).mockRejectedValueOnce(new ApiError(null, "NETWORK_ERROR", "Sem conexão."));
  jest.mocked(request).mockResolvedValueOnce(response);
  fill();
  fireEvent.press(screen.getByText("Confirmar"));
  await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Sem conexão."));
  expect(screen.queryByText("Comprovante simulado")).toBeNull();
  fireEvent.press(screen.getByText("Confirmar"));
  await waitFor(() => expect(screen.getByText("Comprovante simulado")).toBeTruthy());
  expect(jest.mocked(request).mock.calls[1]![1]!.data.idempotency_key).toBe(jest.mocked(request).mock.calls[0]![1]!.data.idempotency_key);
});
test("a second press during a pending request cannot submit another Pix", async () => {
  let complete!: (value: typeof response) => void;
  jest.mocked(request).mockImplementation(() => new Promise(resolve => {complete = resolve as typeof complete;}));
  fill();
  fireEvent.press(screen.getByText("Confirmar"));
  fireEvent.press(screen.getByText("Confirmando…"));
  expect(request).toHaveBeenCalledTimes(1);
  complete(response);
  await waitFor(() => expect(screen.getByText("Comprovante simulado")).toBeTruthy());
});
