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

const { validateApiUrl } = loadFixture("../src/config/validateEnv.ts");
const { formatDecimal, isBalanceResponse } = loadFixture(
  "../src/features/banking/contracts.ts",
);
const { normalizeHttpError } = loadFixture("../src/services/errors.ts");
test("API configuration rejects credentials, invalid schemes and missing version prefixes", () => {
  assert.equal(
    validateApiUrl("http://10.0.2.2:8000/api/v1/"),
    "http://10.0.2.2:8000/api/v1",
  );
  for (const value of [
    undefined,
    "",
    "broken",
    "file:///api/v1",
    "http://a:b@localhost/api/v1",
    "http://localhost/wrong",
  ])
    assert.throws(() => validateApiUrl(value));
});
test("REST monetary strings stay exact at NUMERIC(18,2) boundaries", () => {
  assert.equal(
    formatDecimal("9999999999999999.99"),
    "R$ 9.999.999.999.999.999,99",
  );
  assert.equal(formatDecimal("-0.29"), "−R$ 0,29");
  assert.equal(
    isBalanceResponse({ account_id: "a", currency: "BRL", balance: 0 }, "a"),
    false,
  );
  assert.equal(
    isBalanceResponse(
      { account_id: "a", currency: "BRL", balance: "0.00" },
      "a",
    ),
    true,
  );
});
test("network, timeout, validation and server errors are distinguishable without exposing diagnostics", () => {
  assert.equal(
    normalizeHttpError("ERR_NETWORK", null, undefined).code,
    "NETWORK_ERROR",
  );
  assert.equal(
    normalizeHttpError("ECONNABORTED", null, undefined).code,
    "TIMEOUT",
  );
  assert.equal(
    normalizeHttpError("ERR_CANCELED", null, undefined).code,
    "CANCELLED",
  );
  assert.equal(
    normalizeHttpError(undefined, 422, {
      error: {
        code: "VALIDATION_ERROR",
        message: "Confira os campos.",
        details: [],
      },
      request_id: "test",
    }).requestId,
    "test",
  );
  assert.ok(
    !normalizeHttpError(
      undefined,
      500,
      "private SQL diagnostic",
    ).message.includes("private"),
  );
});
