import type {
  Action,
  Category,
  DemoAlert,
  DemoState,
  ForecastPoint,
  Profile,
  ProfileId,
  Snapshot,
  Transaction,
} from "./types";

export const START_DATE = "2026-10-23";
export const MODEL = "Cenário de interface v0.1";
export const profiles: Profile[] = [
  {
    id: "regular",
    name: "Gisele Santos",
    initials: "GS",
    description: "Renda regular",
    salary: 420000,
    opening: 294753,
  },
  {
    id: "variable",
    name: "Rafael Lima",
    initials: "RL",
    description: "Renda variável",
    salary: 280000,
    opening: 187500,
  },
  {
    id: "tight",
    name: "Ana Costa",
    initials: "AC",
    description: "Orçamento apertado",
    salary: 240000,
    opening: 42000,
  },
];
export function addDays(date: string, days: number): string {
  const value = new Date(`${date}T12:00:00Z`);
  value.setUTCDate(value.getUTCDate() + days);
  return value.toISOString().slice(0, 10);
}
export function money(cents: number): string {
  return (cents / 100).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}
export function dateLabel(date: string): string {
  return new Date(`${date}T12:00:00Z`).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
    timeZone: "UTC",
  });
}
export function parseCents(value: string): number | null {
  const normalized = value.trim();
  if (!/^\d{1,7}([,.]\d{1,2})?$/.test(normalized)) return null;
  const [whole = "", fraction = ""] = normalized.replace(",", ".").split(".");
  const cents = Number(whole) * 100 + Number(fraction.padEnd(2, "0"));
  return Number.isSafeInteger(cents) && cents > 0 ? cents : null;
}
export function balanceOf(
  state: Pick<DemoState, "opening" | "transactions">,
): number {
  return state.transactions.reduce(
    (sum, tx) => sum + (tx.kind === "income" ? tx.cents : -tx.cents),
    state.opening,
  );
}
export function profileOf(id: ProfileId): Profile {
  return profiles.find((p) => p.id === id) ?? profiles[0]!;
}
function scheduled(
  date: string,
  profile: Profile,
): { income: number; expense: number } {
  const day = Number(date.slice(8));
  return {
    income: day === 5 ? profile.salary : 0,
    expense: 4500 + (day === 8 ? 145000 : 0) + (day === 28 ? 42000 : 0),
  };
}
// A deterministic UI fixture, not a trained forecasting engine. It never reads future actuals.
export function projection(state: DemoState, offset = 0): ForecastPoint[] {
  let balance = balanceOf(state) - offset;
  return Array.from({ length: 30 }, (_, index) => {
    const date = addDays(state.date, index + 1);
    const values = scheduled(date, profileOf(state.profileId));
    balance += values.income - values.expense;
    return { date, balance, ...values };
  });
}
export function currentSnapshot(state: DemoState): Snapshot {
  return state.snapshots[state.snapshots.length - 1]!;
}
function capture(state: DemoState, reason: string): DemoState {
  const snapshot: Snapshot = {
    id: `v${state.snapshots.length + 1}`,
    generatedAt: `${state.date}T12:00:00Z`,
    simulatedDate: state.date,
    horizon: 30,
    model: MODEL,
    referenceBalance: balanceOf(state),
    reason,
    points: projection(state),
  };
  const firstRisk = snapshot.points.find((p) => p.balance < 0);
  const alerts: DemoAlert[] = firstRisk
    ? [
        {
          id: `alert-${snapshot.id}`,
          date: state.date,
          title: "Atenção ao saldo nos próximos dias",
          message: `O cenário ilustrativo aponta ${money(firstRisk.balance)} em ${dateLabel(firstRisk.date)}. Revise os gastos previstos. Esta estimativa não é uma garantia.`,
          targetDate: firstRisk.date,
          expectedBalance: firstRisk.balance,
          snapshotId: snapshot.id,
          read: false,
        },
      ]
    : [];
  return {
    ...state,
    snapshots: [...state.snapshots, snapshot],
    alerts: [...alerts, ...state.alerts],
  };
}
export function initialState(
  profileId: ProfileId = "regular",
  seed = 42,
): DemoState {
  const profile = profileOf(profileId);
  let random = seed >>> 0;
  const next = () => {
    random = (Math.imul(random, 1664525) + 1013904223) >>> 0;
    return random;
  };
  const transactions: Transaction[] = [];
  for (let index = 29; index >= 0; index--) {
    const date = addDays(START_DATE, -index);
    const day = Number(date.slice(8));
    if (day === 5)
      transactions.push({
        id: `seed-income-${date}`,
        date,
        description: "Salário · Empresa Horizonte",
        category: "Renda",
        kind: "income",
        cents: profile.salary,
      });
    if (day === 8)
      transactions.push({
        id: `seed-rent-${date}`,
        date,
        description: "Aluguel",
        category: "Moradia",
        kind: "expense",
        cents: 145000,
      });
    if (day === 15)
      transactions.push({
        id: `seed-stream-${date}`,
        date,
        description: "Assinatura de streaming",
        category: "Assinaturas",
        kind: "expense",
        cents: 5590,
      });
    const cents = 2500 + (next() % 6500);
    transactions.push({
      id: `seed-expense-${date}`,
      date,
      description: index % 3 === 0 ? "Mercado do bairro" : "Despesas do dia",
      category: index % 3 === 0 ? "Alimentação" : "Outros",
      kind: "expense",
      cents,
    });
  }
  const net = transactions.reduce(
    (sum, tx) => sum + (tx.kind === "income" ? tx.cents : -tx.cents),
    0,
  );
  return capture(
    {
      profileId,
      seed,
      date: START_DATE,
      opening: profile.opening - net,
      transactions,
      snapshots: [],
      alerts: [],
      processedIds: [],
      notificationsEnabled: true,
    },
    "Cenário inicial",
  );
}
export function validateTransaction(
  state: DemoState,
  tx: Transaction,
): string | null {
  if (
    !tx.id ||
    state.processedIds.includes(tx.id) ||
    state.transactions.some((item) => item.id === tx.id)
  )
    return "Esta movimentação já foi confirmada.";
  if (!Number.isSafeInteger(tx.cents) || tx.cents <= 0 || tx.cents > 999999999)
    return "Informe um valor válido, maior que zero.";
  if (!tx.description.trim() || tx.description.length > 120)
    return "Informe uma descrição com até 120 caracteres.";
  if (tx.date !== state.date)
    return "A data deve corresponder ao dia simulado atual.";
  if (tx.kind !== "income" && tx.cents > balanceOf(state))
    return "Saldo insuficiente para esta movimentação simulada.";
  return null;
}
export function demoReducer(state: DemoState, action: Action): DemoState {
  if (action.type === "reset")
    return initialState(action.profileId, action.seed);
  if (action.type === "preferences")
    return { ...state, notificationsEnabled: action.enabled };
  if (action.type === "read")
    return {
      ...state,
      alerts: state.alerts.map((a) =>
        a.id === action.id ? { ...a, read: true } : a,
      ),
    };
  if (action.type === "transaction") {
    if (validateTransaction(state, action.transaction)) return state;
    return capture(
      {
        ...state,
        transactions: [...state.transactions, action.transaction],
        processedIds: [...state.processedIds, action.transaction.id],
      },
      action.transaction.description,
    );
  }
  if (!Number.isInteger(action.days) || action.days < 1 || action.days > 30)
    return state;
  let next = state;
  for (let day = 0; day < action.days; day++) {
    const date = addDays(next.date, 1);
    const planned = scheduled(date, profileOf(state.profileId));
    // Future realized fixtures are materialized only when the simulated clock advances.
    const transactions: Transaction[] = [
      {
        id: `daily-${date}`,
        date,
        description: "Despesas realizadas · dia simulado",
        category: "Outros" as Category,
        kind: "expense",
        cents:
          planned.expense +
          1500 +
          ((state.seed + Number(date.slice(8))) % 7) * 100,
      },
    ];
    if (planned.income)
      transactions.push({
        id: `income-${date}`,
        date,
        description: "Receita recorrente simulada",
        category: "Renda",
        kind: "income",
        cents: planned.income,
      });
    next = {
      ...next,
      date,
      transactions: [...next.transactions, ...transactions],
    };
  }
  return capture(next, `Avanço de ${action.days} dia(s)`);
}
export function realizedBalance(state: DemoState, date: string): number | null {
  if (date > state.date) return null;
  return balanceOf({
    opening: state.opening,
    transactions: state.transactions.filter((tx) => tx.date <= date),
  });
}
