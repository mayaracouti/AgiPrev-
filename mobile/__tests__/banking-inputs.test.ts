import {decimalInput, idempotencyKey} from "@/features/banking/inputs";

test.each([["10,29", "10.29"], ["1", "1.00"], ["0,01", "0.01"], ["9999999999999999,99", "9999999999999999.99"], ["0", null], ["-1", null], ["1.001", null], ["1e3", null], ["1.000,00", null]])("money input %s", (input, expected) => {
  expect(decimalInput(input!)).toBe(expected);
});
test("request identifiers are UUIDs and separate operations get different keys", () => {
  const key = idempotencyKey();
  expect(key).toMatch(/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/);
  expect(idempotencyKey()).not.toBe(key);
});
