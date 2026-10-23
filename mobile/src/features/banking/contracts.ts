export interface Customer {
  id: string;
  name: string;
  email: string;
  demo_profile: string;
}
export interface Account {
  id: string;
  customer_id: string;
  currency: "BRL";
}
export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  expires_at: string;
  customer: Customer;
  accounts: Account[];
}
export interface BalanceResponse {
  account_id: string;
  currency: "BRL";
  balance: string;
}
export interface LedgerEntry {
  id: string;
  occurred_on: string;
  direction: "credit" | "debit";
  amount: string;
  description: string;
}
export function isBalanceResponse(
  value: unknown,
  accountId: string,
): value is BalanceResponse {
  if (!value || typeof value !== "object") return false;
  return (
    "account_id" in value &&
    value.account_id === accountId &&
    "currency" in value &&
    value.currency === "BRL" &&
    "balance" in value &&
    typeof value.balance === "string" &&
    /^-?\d{1,16}\.\d{2}$/.test(value.balance)
  );
}
// No floating-point arithmetic on REST monetary values, including values above Number.MAX_SAFE_INTEGER.
export function formatDecimal(value: string): string {
  if (!/^-?\d+\.\d{2}$/.test(value))
    throw new Error("Valor monetário inválido.");
  const [whole = "0", fraction = "00"] = value.split(".");
  const negative = whole.startsWith("-");
  return `${negative ? "−" : ""}R$ ${whole.replace("-", "").replace(/\B(?=(\d{3})+(?!\d))/g, ".")},${fraction}`;
}

export interface Category { id: string; name: string }
export interface BankTransaction extends LedgerEntry {
  category_id: string;
  kind: string;
  recipient: string | null;
}
export interface TransactionPage { items: BankTransaction[]; next_cursor: string | null; total: number }
export interface Receipt { transaction: BankTransaction; balance: string; simulated: true }
export interface Scenario {
  id: string; current_date: string; seed: number; version: string; balance: string;
  pending_events: {id: string; date: string; kind: string; amount: string; direction: string; description: string; scheduled_balance: string}[];
}
export const financialProfiles = ["regular", "variable", "tight", "retired", "entrepreneur", "seasonal"] as const;
export const profileNames: Record<string, string> = {
  regular: "Renda regular", variable: "Renda variável", tight: "Orçamento apertado",
  retired: "Aposentadoria fictícia", entrepreneur: "Empreendedor", seasonal: "Renda sazonal",
};
