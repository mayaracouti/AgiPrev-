// Keys identify requests, never credentials. Persist the same key throughout a retry.
export function idempotencyKey(): string {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
    const value = Math.floor(Math.random() * 16);
    return (char === "x" ? value : (value & 3) | 8).toString(16);
  });
}
export function decimalInput(value: string): string | null {
  const normalized = value.trim().replace(",", ".");
  if (!/^(?:0|[1-9]\d{0,15})(?:\.\d{1,2})?$/.test(normalized)) return null;
  const [whole, cents = ""] = normalized.split(".");
  const result = `${whole}.${cents.padEnd(2, "0")}`;
  return /^0\.00$/.test(result) ? null : result;
}
