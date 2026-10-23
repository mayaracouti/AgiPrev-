import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/auth/AuthProvider";
import { request } from "@/services/http";
import { ApiError, errorMessage } from "@/services/errors";
import type { LedgerEntry } from "./contracts";
export function useLedger() {
  const { session } = useAuth();
  const account = session?.accounts[0]?.id;
  const [page, setPage] = useState(0);
  const [version, setVersion] = useState(0);
  const [result, setResult] = useState<{
    key: string;
    entries: LedgerEntry[];
    error: string | null;
  } | null>(null);
  const key = `${account}:${page}:${version}`;
  const refresh = useCallback(() => setVersion((value) => value + 1), []);
  useEffect(() => {
    if (!account) return;
    const controller = new AbortController();
    void request<LedgerEntry[]>(
      `/accounts/${account}/ledger?limit=50&offset=${page * 50}`,
      { signal: controller.signal },
    )
      .then((data) => {
        if (
          !Array.isArray(data) ||
          data.some(
            (item) =>
              !item.id ||
              !["credit", "debit"].includes(item.direction) ||
              !/^\d+\.\d{2}$/.test(item.amount),
          )
        )
          throw new ApiError(
            null,
            "INVALID_RESPONSE",
            "O servidor retornou um extrato inválido.",
          );
        if (!controller.signal.aborted)
          setResult({ key, entries: data, error: null });
      })
      .catch((cause) => {
        if (!controller.signal.aborted)
          setResult({ key, entries: [], error: errorMessage(cause) });
      });
    return () => controller.abort();
  }, [account, page, version, key]);
  const current = result?.key === key ? result : null;
  return {
    entries: current?.entries ?? [],
    loading: Boolean(account && !current),
    error: current?.error ?? null,
    refresh,
    page,
    setPage,
  };
}
