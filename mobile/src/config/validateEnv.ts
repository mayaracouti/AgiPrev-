export function validateApiUrl(value: string | undefined): string {
  if (!value)
    throw new Error("Configure EXPO_PUBLIC_API_URL no arquivo .env do mobile.");
  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    throw new Error("EXPO_PUBLIC_API_URL deve ser uma URL HTTP(S) válida.");
  }
  if (
    !["http:", "https:"].includes(parsed.protocol) ||
    parsed.username ||
    parsed.password ||
    parsed.search ||
    parsed.hash ||
    parsed.pathname.replace(/\/$/, "") !== "/api/v1"
  ) {
    throw new Error(
      "Use uma URL HTTP(S) terminada em /api/v1, sem credenciais, query ou fragmento.",
    );
  }
  return value.replace(/\/$/, "");
}
