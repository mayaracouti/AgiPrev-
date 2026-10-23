const { test } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { resolve } = require("node:path");
const ts = require("typescript");

// Execute the pure TypeScript fixtures without loading React Native or a native runtime.
function loadFixture(path) {
  const source = readFileSync(resolve(__dirname, path), "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
    },
  });
  const exports = {};
  new Function("exports", compiled.outputText)(exports);
  return exports;
}
const {
  initialState,
  balanceOf,
  demoReducer,
  currentSnapshot,
  parseCents,
  projection,
  realizedBalance,
  validateTransaction,
} = loadFixture("../src/demo/model.ts");
const { prepareReport } = loadFixture("../src/features/evaluation/report.ts");

const transaction = (state) => ({
  id: "test-pix",
  date: state.date,
  description: "Pix fictício",
  category: "Pix",
  kind: "pix",
  cents: 12345,
});

test("money input preserves cents and rejects ambiguous, zero and invalid values", () => {
  assert.equal(parseCents("0,29"), 29);
  assert.equal(parseCents("120.5"), 12050);
  for (const value of [
    "0",
    "-1",
    "NaN",
    "1.000,00",
    "1e3",
    "1,234",
    "",
    "10000000",
  ])
    assert.equal(parseCents(value), null);
});
test("synthetic histories are deterministic for the same profile and seed", () => {
  assert.deepEqual(initialState("regular", 42), initialState("regular", 42));
  assert.notDeepEqual(
    initialState("regular", 42).transactions,
    initialState("regular", 43).transactions,
  );
  assert.equal(balanceOf(initialState("tight")), 42000);
});
test("a confirmed debit updates balance and projection exactly once and keeps old forecasts", () => {
  const before = initialState();
  const original = JSON.stringify(currentSnapshot(before));
  const tx = transaction(before);
  const after = demoReducer(before, { type: "transaction", transaction: tx });
  assert.equal(balanceOf(after), balanceOf(before) - tx.cents);
  assert.equal(
    currentSnapshot(after).points[0].balance,
    currentSnapshot(before).points[0].balance - tx.cents,
  );
  assert.equal(JSON.stringify(after.snapshots[0]), original);
  assert.equal(after.snapshots.length, before.snapshots.length + 1);
  assert.equal(
    demoReducer(after, { type: "transaction", transaction: tx }),
    after,
  );
});
test("invalid and insufficient transactions leave the state unchanged", () => {
  const before = initialState();
  const tx = transaction(before);
  for (const invalid of [
    { ...tx, cents: -10 },
    { ...tx, cents: 1.5 },
    { ...tx, cents: balanceOf(before) + 1 },
    { ...tx, description: "" },
    { ...tx, date: "2030-01-01" },
  ]) {
    assert.ok(validateTransaction(before, invalid));
    assert.equal(
      demoReducer(before, { type: "transaction", transaction: invalid }),
      before,
    );
  }
});
test("advancing time materializes actuals only through the simulated current date", () => {
  const before = initialState();
  const original = JSON.stringify(before.snapshots[0]);
  assert.equal(realizedBalance(before, "2026-10-24"), null);
  const after = demoReducer(before, { type: "advance", days: 7 });
  assert.equal(after.date, "2026-10-30");
  assert.ok(after.transactions.every((tx) => tx.date <= after.date));
  assert.notEqual(realizedBalance(after, "2026-10-24"), null);
  assert.equal(JSON.stringify(after.snapshots[0]), original);
  assert.equal(realizedBalance(after, "2026-10-31"), null);
  assert.equal(demoReducer(before, { type: "advance", days: -1 }), before);
});
test("a hypothetical scenario does not debit or create saved forecast versions", () => {
  const state = initialState();
  const before = JSON.stringify(state);
  const baseline = projection(state);
  const scenario = projection(state, 50000);
  assert.equal(scenario[0].balance, baseline[0].balance - 50000);
  assert.equal(JSON.stringify(state), before);
});
test("report previews never fabricate evaluation metrics or a completed backtest", () => {
  const report = prepareReport({
    profile: "regular",
    seed: 42,
    horizon: 7,
    model: "Média histórica",
    cutoff: "2026-10-23",
  });
  assert.equal(report.status, "awaiting_backend");
  assert.ok(Object.values(report.metrics).every((value) => value === null));
  assert.equal(report.recalculationP95Ms, null);
});
