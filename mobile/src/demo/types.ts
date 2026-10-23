export type ProfileId = "regular" | "variable" | "tight";
export type TransactionKind = "income" | "expense" | "pix";
export type Category =
  | "Renda"
  | "Moradia"
  | "Alimentação"
  | "Transporte"
  | "Saúde"
  | "Assinaturas"
  | "Pix"
  | "Outros";
export const categories: Category[] = [
  "Renda",
  "Moradia",
  "Alimentação",
  "Transporte",
  "Saúde",
  "Assinaturas",
  "Pix",
  "Outros",
];
export interface Profile {
  id: ProfileId;
  name: string;
  initials: string;
  description: string;
  salary: number;
  opening: number;
}
export interface Transaction {
  id: string;
  date: string;
  description: string;
  category: Category;
  kind: TransactionKind;
  cents: number;
}
export interface ForecastPoint {
  date: string;
  balance: number;
  income: number;
  expense: number;
}
export interface Snapshot {
  id: string;
  generatedAt: string;
  simulatedDate: string;
  horizon: 30;
  model: string;
  referenceBalance: number;
  reason: string;
  points: ForecastPoint[];
}
export interface DemoAlert {
  id: string;
  date: string;
  title: string;
  message: string;
  targetDate: string;
  expectedBalance: number;
  snapshotId: string;
  read: boolean;
}
export interface DemoState {
  profileId: ProfileId;
  seed: number;
  date: string;
  opening: number;
  transactions: Transaction[];
  snapshots: Snapshot[];
  alerts: DemoAlert[];
  processedIds: string[];
  notificationsEnabled: boolean;
}
export type Action =
  | { type: "transaction"; transaction: Transaction }
  | { type: "advance"; days: number }
  | { type: "read"; id: string }
  | { type: "preferences"; enabled: boolean }
  | { type: "reset"; profileId: ProfileId; seed: number };
