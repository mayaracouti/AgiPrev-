import { fireEvent, render, screen } from "@testing-library/react-native";
import { BalanceCard } from "@/features/banking/components/BalanceCard";

jest.mock("expo-router", () => ({
  router: { push: jest.fn(), replace: jest.fn() },
}));
const balance = {
  account_id: "demo-account",
  currency: "BRL" as const,
  balance: "0.00",
};

test("shows an exact zero balance without replacing it with a fixture", () => {
  render(
    <BalanceCard
      data={balance}
      loading={false}
      error={null}
      onRetry={jest.fn()}
    />,
  );
  expect(screen.getByTestId("account-balance")).toHaveTextContent("R$ 0,00");
});
test("loading does not show stale amounts", () => {
  render(
    <BalanceCard data={balance} loading error={null} onRetry={jest.fn()} />,
  );
  expect(screen.getByLabelText("Carregando saldo")).toBeTruthy();
  expect(screen.queryByTestId("account-balance")).toBeNull();
});
test("errors are readable and retry works without a fake balance", () => {
  const retry = jest.fn();
  render(
    <BalanceCard
      data={null}
      loading={false}
      error="Sem conexão com a API."
      onRetry={retry}
    />,
  );
  expect(screen.getByRole("alert")).toHaveTextContent("Sem conexão com a API.");
  fireEvent.press(screen.getByText("Tentar novamente"));
  expect(retry).toHaveBeenCalledTimes(1);
  expect(screen.queryByTestId("account-balance")).toBeNull();
});
test("a hidden balance remains hidden", () => {
  render(
    <BalanceCard
      data={balance}
      loading={false}
      error={null}
      visible={false}
      onRetry={jest.fn()}
    />,
  );
  expect(screen.getByTestId("account-balance")).toHaveTextContent("R$ ••••••");
});
test("missing account has an explicit empty state", () => {
  render(
    <BalanceCard
      data={null}
      loading={false}
      error={null}
      onRetry={jest.fn()}
    />,
  );
  expect(screen.getByText("Nenhuma conta disponível.")).toBeTruthy();
});
